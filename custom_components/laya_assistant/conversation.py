"""Laya-backed conversation entity with an explicit HA entity allowlist."""

import asyncio
import logging
import math
from time import monotonic

from homeassistant.auth.permissions.const import POLICY_CONTROL, POLICY_READ
from homeassistant.components import conversation
from homeassistant.core import HomeAssistantError
from homeassistant.helpers import intent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util, ulid

from .catalog import build_targets, caller_area
from .client import LayaClient, LayaConnectionError
from .const import (
    CONF_API_KEY, CONF_CLIMATES, CONF_DEBUG, CONF_FANS, CONF_LIGHTS, CONF_PROVIDER,
    CONF_SATELLITE, CONF_SWITCHES, CONF_URL, PROVIDER_JEV, PROVIDER_LAYA,
)
from .diagnostics import format_debug, summarize_answers
from .locale import DONE_ACTIONS, get_locale
from .routing import (
    Thresholds, best_action, detail_request, domain_request,
    selected_domain, selected_target, target_candidates, target_request, valid_target,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([LayaConversation(entry)])


class LayaConversation(conversation.ConversationEntity):
    _attr_name = "Laya Assistant"

    def __init__(self, entry):
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        if entry.data.get(CONF_PROVIDER, PROVIDER_LAYA) == PROVIDER_JEV:
            self._attr_name = "Laya Assistant (Jev)"
        self.metrics = {}
        self.lock = asyncio.Lock()

    @property
    def supported_languages(self):
        # HA supplies its current language; unsupported locales use English.
        return "*"

    @property
    def supported_features(self):
        settings = {**self.entry.data, **self.entry.options}
        return (conversation.ConversationEntityFeature.CONTROL
                if any(settings.get(field) for field in (CONF_LIGHTS, CONF_SWITCHES, CONF_FANS, CONF_CLIMATES))
                else 0)

    @property
    def extra_state_attributes(self):
        return self.metrics

    async def async_process(self, user_input):
        async with self.lock:
            return await self._process(user_input)

    async def _process(self, user_input):
        start = monotonic()
        locale = get_locale(user_input.language)
        language = locale.code
        response = intent.IntentResponse(language=user_input.language)
        self.metrics = {"status": "processing"}
        settings = {**self.entry.data, **self.entry.options}
        debug_enabled = settings.get(CONF_DEBUG) is True
        trace = {"thresholds": {}, "stages": {}, "decisions": {}}

        def finish(text, *, error=False, query=False):
            self.metrics["api_ms"] = sum(self.metrics.get(key, 0) for key in
                                         ("domain_ms", "target_ms", "detail_ms"))
            self.metrics["total_ms"] = round((monotonic() - start) * 1000)
            if debug_enabled:
                self.metrics["debug"] = trace
                text += "\n" + format_debug(trace, self.metrics)
            if error:
                response.async_set_error(intent.IntentResponseErrorCode.FAILED_TO_HANDLE, text)
            response.async_set_speech(text)
            if query:
                response.response_type = intent.IntentResponseType.QUERY_ANSWER
            self.async_write_ha_state()
            return conversation.ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id or ulid.ulid_now(),
            )

        text = user_input.text.strip()
        if not text or len(text) > 500:
            self.metrics["status"] = "rejected"
            trace["reason"] = "invalid_input"
            return finish(locale.replies[2], error=True)
        try:
            thresholds = Thresholds.from_settings(settings)
            trace["thresholds"] = thresholds.as_dict()
            trace["soft_thresholds"] = thresholds.soft_dict()
            trace["provider"] = settings.get(CONF_PROVIDER, PROVIDER_LAYA)
            targets = build_targets(self.hass, settings, language)
            area = caller_area(self.hass, user_input.device_id or settings.get(CONF_SATELLITE))
            client = LayaClient(async_get_clientsession(self.hass), settings[CONF_URL],
                                settings.get(CONF_API_KEY, ""),
                                settings.get(CONF_PROVIDER, PROVIDER_LAYA))
            self.metrics["caller_area"] = area

            async def ask(request, name):
                started = monotonic()
                answers = await client.ask(request)
                self.metrics[name] = round((monotonic() - started) * 1000)
                if debug_enabled:
                    trace["stages"][name.removesuffix("_ms")] = summarize_answers(answers)
                return answers

            first = await ask(domain_request(text, language), "domain_ms")
            domain = selected_domain(first.get("domain"), text, language, thresholds)
            trace["decisions"]["domain"] = domain
            if domain not in {"on_off", "temperature", "time"}:
                self.metrics["status"] = "clarification"
                trace["reason"] = "domain_rejected"
                return finish(locale.replies[0])
            self.metrics["domain"] = domain

            target = None
            if domain != "time":
                candidates = target_candidates(text, domain, targets, area, language)
                if debug_enabled:
                    trace["candidates"] = {item.key: {
                        "name": item.label, "area": item.area, "entities": list(item.entities),
                        "labels": list(item.aliases),
                    } for item in candidates}
                if not candidates or len(candidates) > 48:
                    self.metrics["status"] = "clarification"
                    trace["reason"] = "no_allowed_target"
                    return finish(locale.replies[0])
                request = target_request(text, domain, candidates, area, language)
                second = await ask(request, "target_ms")
                target = selected_target(second, text, candidates, language, thresholds)
                trace["decisions"]["target"] = target.key if target else None
                if target is None or not valid_target(target, text, area, targets, language):
                    self.metrics["status"] = "clarification"
                    trace["reason"] = "target_rejected"
                    return finish(locale.replies[0])
                self.metrics["target"] = target.entities if len(target.entities) > 1 else target.entities[0]

            self.metrics["api_ms"] = sum(self.metrics.get(key, 0) for key in ("domain_ms", "target_ms", "detail_ms"))
            if domain == "time":
                now = dt_util.now()
                self.metrics["status"] = "answered"
                return finish(locale.replies[7].format(time=now.strftime("%H:%M")), query=True)
            if domain == "temperature":
                entity_id = target.entities[0]
                if not await self._permitted(user_input, (entity_id,), POLICY_READ):
                    self.metrics["status"] = "denied"
                    trace["reason"] = "permission_denied"
                    return finish(locale.replies[3], error=True)
                state = self.hass.states.get(entity_id)
                raw = state.attributes.get("current_temperature") if state and entity_id.startswith("climate.") else state.state if state else None
                try:
                    value = float(raw)
                except (ValueError, TypeError):
                    value = math.nan
                if not math.isfinite(value):
                    self.metrics["status"] = "unavailable"
                    trace["reason"] = "sensor_unavailable"
                    return finish(locale.replies[5], error=True)
                unit = state.attributes.get("unit_of_measurement", "°C")
                self.metrics["status"] = "answered"
                return finish(locale.replies[8].format(target=target.label, value=f"{value:g}", unit=unit), query=True)

            third = await ask(detail_request(text, domain, language), "detail_ms")
            self.metrics["api_ms"] = sum(self.metrics.get(key, 0) for key in ("domain_ms", "target_ms", "detail_ms"))
            action = best_action(third, text, language, thresholds)
            trace["decisions"]["detail"] = action
            if action is None:
                self.metrics["status"] = "clarification"
                trace["reason"] = "action_rejected"
                return finish(locale.replies[0])
            if not await self._permitted(user_input, target.entities, POLICY_CONTROL):
                self.metrics["status"] = "denied"
                trace["reason"] = "permission_denied"
                return finish(locale.replies[4], error=True)
            for entity_id in target.entities:
                state = self.hass.states.get(entity_id)
                if state is None or state.state in {"unavailable", "unknown"}:
                    self.metrics["status"] = "unavailable"
                    trace["reason"] = "target_unavailable"
                    return finish(locale.replies[6], error=True)
            for entity_id in target.entities:
                service_domain = entity_id.split(".", 1)[0]
                if service_domain not in {"light", "switch", "fan", "climate"}:
                    raise ValueError("Disallowed service domain")
                await self.hass.services.async_call(
                    service_domain, action, {"entity_id": entity_id},
                    blocking=True, context=user_input.context,
                )
            self.metrics.update(status="sent", action=action)
            label = target.label
            action_word = DONE_ACTIONS[language][0 if action == "turn_on" else 1]
            return finish(locale.replies[9].format(target=label, action=action_word))
        except (LayaConnectionError, HomeAssistantError, ValueError, TypeError):
            _LOGGER.warning("Laya Assistant request failed")
            self.metrics["status"] = "error"
            trace["reason"] = "request_failed"
            return finish(locale.replies[1], error=True)

    async def _permitted(self, user_input, entities: tuple[str, ...], policy: str) -> bool:
        user_id = user_input.context.user_id
        if not user_id:
            return False
        user = await self.hass.auth.async_get_user(user_id)
        return bool(user and user.is_active and all(
            user.permissions.check_entity(entity_id, policy) for entity_id in entities
        ))

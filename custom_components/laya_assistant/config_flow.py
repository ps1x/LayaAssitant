"""UI setup and allowlist management for Laya Assistant."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import LayaClient, LayaConnectionError, normalize_url
from .aliases import parse_area_overrides, parse_spoken_names
from .const import (
    CONF_API_KEY, CONF_CLIMATES, CONF_DEBUG, CONF_FANS, CONF_LIGHTS, CONF_SATELLITE,
    CONF_SPOKEN_NAMES, CONF_SWITCHES, CONF_TEMPERATURE, CONF_URL, DOMAIN, ENTITY_FIELDS,
    THRESHOLD_DEFAULTS,
)
from .routing import Thresholds


def _entities_schema(current: dict | None = None) -> vol.Schema:
    current = current or {}
    specs = (
        (CONF_LIGHTS, ["light", "switch"]),
        (CONF_SWITCHES, ["switch"]),
        (CONF_FANS, ["fan"]),
        (CONF_CLIMATES, ["climate"]),
        (CONF_TEMPERATURE, ["sensor", "climate"]),
    )
    schema = {}
    for field, domains in specs:
        schema[vol.Optional(field, default=current.get(field, []))] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=domains, multiple=True)
        )
    schema[vol.Optional(CONF_SATELLITE, description={"suggested_value": current.get(CONF_SATELLITE)})] = selector.DeviceSelector()
    schema[vol.Optional(CONF_SPOKEN_NAMES, default=current.get(CONF_SPOKEN_NAMES, "{}"))] = selector.TextSelector(
        selector.TextSelectorConfig(multiline=True)
    )
    schema[vol.Optional(CONF_DEBUG, default=current.get(CONF_DEBUG, False))] = selector.BooleanSelector()
    for key, default in THRESHOLD_DEFAULTS.items():
        schema[vol.Optional(key, default=current.get(key, default))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode=selector.NumberSelectorMode.BOX)
        )
    return vol.Schema(schema)


def _valid_entities(data: dict) -> bool:
    allowed = {
        CONF_LIGHTS: {"light", "switch"}, CONF_SWITCHES: {"switch"},
        CONF_FANS: {"fan"}, CONF_CLIMATES: {"climate"},
        CONF_TEMPERATURE: {"sensor", "climate"},
    }
    selected = {}
    for field in ENTITY_FIELDS:
        values = data.get(field, [])
        if not isinstance(values, list) or any(
            not isinstance(entity, str) or entity.split(".", 1)[0] not in allowed[field]
            for entity in values
        ):
            return False
        selected[field] = values
    control = [entity for field in (CONF_LIGHTS, CONF_SWITCHES, CONF_FANS, CONF_CLIMATES)
               for entity in selected[field]]
    try:
        parse_spoken_names(data.get(CONF_SPOKEN_NAMES), "en")
        parse_area_overrides(data.get(CONF_SPOKEN_NAMES), {
            entity_id for values in selected.values() for entity_id in values
        })
        Thresholds.from_settings(data)
    except (ValueError, TypeError):
        return False
    return (isinstance(data.get(CONF_DEBUG, False), bool)
            and any(selected.values()) and len(control) == len(set(control))
            and all(len(values) == len(set(values)) for values in selected.values()))


class LayaAssistantFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(entry):
        return LayaAssistantOptionsFlow(entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                url = normalize_url(user_input[CONF_URL])
                await LayaClient(async_get_clientsession(self.hass), url, user_input.get(CONF_API_KEY, "")).check()
            except ValueError:
                errors["base"] = "invalid_url"
            except LayaConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                self._connection = {CONF_URL: url, CONF_API_KEY: user_input.get(CONF_API_KEY, "")}
                return await self.async_step_entities()
        return self.async_show_form(
            step_id="user", errors=errors,
            data_schema=vol.Schema({
                vol.Required(CONF_URL): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.URL)),
                vol.Optional(CONF_API_KEY, default=""): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
            }),
        )

    async def async_step_entities(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not _valid_entities(user_input):
                errors["base"] = "select_entities"
            else:
                return self.async_create_entry(title="Laya Assistant", data={**self._connection, **user_input})
        return self.async_show_form(step_id="entities", data_schema=_entities_schema(), errors=errors)


class LayaAssistantOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        current = {**self.entry.data, **self.entry.options}
        errors = {}
        if user_input is not None:
            if not _valid_entities(user_input):
                errors["base"] = "select_entities"
            else:
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=_entities_schema(current), errors=errors)

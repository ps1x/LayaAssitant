"""Pure, fail-closed routing for the Laya conversation agent."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re

from .const import THRESHOLD_DEFAULTS
from .locale import WHOLE_HOME_TERMS, get_locale


@dataclass(frozen=True)
class Target:
    """A user-approved HA target or a group of approved lights."""

    key: str
    label: str
    entities: tuple[str, ...]
    area: str | None
    kind: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Thresholds:
    """Per-stage gates; defaults preserve the original routing behavior."""

    domain_confidence: float = 0.8
    domain_probability: float = 0.8
    target_confidence: float = 0.8
    target_probability: float = 0.8
    action_confidence: float = 0.8
    action_probability: float = 0.8
    temperature_confidence: float = 0.3
    temperature_probability: float = 0.8

    @classmethod
    def from_settings(cls, settings: dict) -> "Thresholds":
        values = {}
        for key, default in THRESHOLD_DEFAULTS.items():
            value = settings.get(key, default)
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Invalid Laya threshold: {key}")
            values[key] = float(value)
        return cls(**values)

    def as_dict(self) -> dict[str, float]:
        return {key: getattr(self, key) for key in THRESHOLD_DEFAULTS}

    def soft_dict(self) -> dict[str, float]:
        """Thresholds for text-anchored exceptions, derived from user settings."""
        return {
            "light_domain_confidence": max(0, self.domain_confidence - 0.2),
            "light_domain_probability": self.domain_probability,
            "room_target_confidence": max(0, self.target_confidence - 0.15),
            "room_target_probability": min(1, self.target_probability + 0.1),
            "fixture_target_confidence": max(0, self.target_confidence - 0.05),
            "fixture_target_probability": min(1, self.target_probability + 0.1),
            "unnamed_temperature_confidence": min(1, self.temperature_confidence + 0.3),
        }


def choice(answer: object, min_confidence: float = 0.8,
           min_probability: float = 0.8) -> str | None:
    """Accept only a finite, high-confidence selected choice."""
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        return None
    selected = answer.get("choice")
    probabilities = answer.get("probabilities")
    if not isinstance(selected, str) or not isinstance(probabilities, dict):
        return None
    probability = probabilities.get(selected)
    confidence = answer.get("confidence")
    for number, threshold in ((probability, min_probability), (confidence, min_confidence)):
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            return None
        if not math.isfinite(number) or not threshold <= number <= 1:
            return None
    return selected


def _soft_choice(answer: object, min_confidence: float, min_probability: float) -> str | None:
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        return None
    selected = answer.get("choice")
    probabilities = answer.get("probabilities")
    if not isinstance(selected, str) or not isinstance(probabilities, dict):
        return None
    confidence = answer.get("confidence")
    probability = probabilities.get(selected)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           or not 0 <= v <= 1 for v in (confidence, probability)):
        return None
    return selected if confidence >= min_confidence and probability >= min_probability else None


def _words(text: str) -> list[str]:
    return re.findall(r"[\w]+", text.casefold(), flags=re.UNICODE)


def _russian(text: str) -> bool:
    return bool(re.search(r"[а-яё]", text.casefold()))


def _wire(text: str, questions: dict, locale, *, target: bool = False) -> dict:
    """Latin non-English inputs must not auto-route to the English checkpoint."""
    request = {
        "state": text if target and locale.code == "ur" else {"request": text},
        "questions": questions,
    }
    if locale.code != "en":
        request["model"] = "multilingual"
    return request


def light_group_label(area: str, language: str | None = None) -> str:
    """A short spoken label; HA area names stay the source of truth."""
    lower = area.casefold()
    locale = get_locale(language)
    if locale.code != "ru" or not _russian(area):
        return locale.light_template.format(area=area)
    if lower.endswith("ая"):
        location = area[:-2] + "ой"
    elif lower.endswith("ня"):
        location = area[:-2] + "не"
    elif lower.endswith("а"):
        location = area[:-1] + "е"
    elif lower.endswith("ь"):
        location = area[:-1] + "и"
    else:
        location = area + "е"
    preposition = "на" if lower.startswith("кухн") else "в"
    return f"свет {preposition} {location.casefold()}"


def _russian_genitive(area: str) -> str:
    name = area.casefold()
    if name.endswith("ая"):
        return name[:-2] + "ой"
    if name.endswith("ня"):
        return name[:-1] + "и"
    if name.endswith("а"):
        return name[:-1] + "ы"
    if name.endswith("ь"):
        return name[:-1] + "и"
    return name + "а"


def mentioned_area(text: str, areas: set[str]) -> str | None:
    """Find one explicit area using its full name or a conservative stem."""
    words = _words(text)
    found = []
    for area in areas:
        name = area.casefold().strip()
        if not name:
            continue
        parts = _words(name)
        if not parts:
            continue
        if name in text.casefold():
            found.append(area)
            continue
        # Russian inflection: Детская -> детской, Кухня -> кухне.
        if len(parts) == 1 and len(parts[0]) >= 5 and any(
            word.startswith(parts[0][:-2]) for word in words
        ):
            found.append(area)
            continue
        if len(parts) > 1:
            significant = [part for part in parts if len(part) >= 4]
            if significant and all(any(word.startswith(part[:3]) for word in words) for part in significant):
                found.append(area)
    return found[0] if len(found) == 1 else None


def explicit_action(text: str, language: str | None = None) -> str | None:
    """Return an obvious verb only as a veto against a model contradiction."""
    words = text.casefold()
    locale = get_locale(language or ("ru" if _russian(text) else "en"))
    def contains(term):
        term = term.casefold()
        if re.fullmatch(r"[a-zà-ÿ\s-]+", term):
            return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", words))
        return term in words
    on = any(contains(term) for term in locale.on_terms)
    off = any(contains(term) for term in locale.off_terms)
    return "turn_on" if on and not off else "turn_off" if off and not on else None


def is_light_request(text: str, language: str | None = None) -> bool:
    locale = get_locale(language or ("ru" if _russian(text) else "en"))
    words = text.casefold()
    return any(term.casefold() in words for term in locale.light_terms)


def selected_domain(answer: object, text: str, language: str | None = None,
                    thresholds: Thresholds | None = None) -> str | None:
    gates = thresholds or Thresholds()
    strict = choice(answer, gates.domain_confidence, gates.domain_probability)
    if strict:
        return strict
    # A direct spoken light command anchors a hesitant on/off choice; later
    # target and action stages still have to agree and pass their own checks.
    if explicit_action(text, language) and is_light_request(text, language):
        soft_gates = gates.soft_dict()
        soft = _soft_choice(answer, soft_gates["light_domain_confidence"],
                            soft_gates["light_domain_probability"])
        if soft == "on_off":
            return soft
    return None


def is_specific_light_request(text: str, individuals: list[Target], area: str | None,
                              language: str | None = None) -> bool:
    """Look for a fixture word beyond the room and generic light words."""
    ignored = {"свет", "света", "свете", "освещение", "освещения", "лампа", "лампы",
               "light", "lights", "lamp", "lamps", "весь", "все", "всё", "all"}
    text_words = set(_words(text))
    area_words = set(_words(area or ""))
    area_stems = {word[:3] for word in area_words if len(word) >= 4}
    locale = get_locale(language)
    for target in individuals:
        if area and target.area != area:
            continue
        name_words = {word for name in (target.label, *target.aliases) for word in _words(name)
                      if word not in ignored and word not in area_words
                      and not any(word.startswith(stem) for stem in area_stems)}
        for token in name_words:
            if len(token) >= 4 and any(word.startswith(token[:4]) for word in text_words):
                return True
        if locale.code == "zh":
            for name in (target.label, *target.aliases):
                descriptor = name.casefold().replace((area or "").casefold(), "")
                for term in locale.light_terms:
                    descriptor = descriptor.replace(term.casefold(), "")
                descriptor = descriptor.strip()
                if descriptor and descriptor in text.casefold():
                    return True
    return False


def whole_home_request(text: str, language: str | None = None) -> bool:
    locale = get_locale(language)
    return any(term.casefold() in text.casefold() for term in WHOLE_HOME_TERMS[locale.code])


def domain_request(text: str, language: str | None = None) -> dict:
    locale = get_locale(language or ("ru" if _russian(text) else "en"))
    return _wire(text, {"domain": {
            "type": "choice",
            "instructions": locale.domain_prompt,
            "criteria": dict(zip(("on_off", "temperature", "time", "none"), locale.domain_criteria)),
        }}, locale)


def target_candidates(
    text: str, domain: str, targets: list[Target], caller_area: str | None,
    language: str | None = None,
) -> list[Target]:
    """Limit candidates by capability and explicit area, without choosing one."""
    area = mentioned_area(text, {t.area for t in targets if t.area})
    if domain == "temperature":
        candidates = [t for t in targets if t.kind == "temperature"]
        return [t for t in candidates if t.area == area] if area else candidates
    if domain != "on_off":
        return []
    light_groups = [t for t in targets if t.kind == "light_group"]
    light_entities = [t for t in targets if t.kind == "light_entity"]
    if is_light_request(text, language):
        if whole_home_request(text, language) and not area:
            return [t for t in targets if t.kind == "all_lights"]
        room = area or caller_area
        if is_specific_light_request(text, light_entities, room, language):
            return ([t for t in light_groups if t.area == room]
                    + [t for t in light_entities if t.area == room])
        return light_groups
    return [t for t in targets if t.kind in {"light_entity", "switch", "fan", "climate"}]


_URDU_ROOM_GLOSSES = {
    "سونے کا کمرہ": "bedroom", "باورچی خانہ": "kitchen",
    "رہنے کا کمرہ": "living room", "غسل خانہ": "bathroom",
    "بچوں کا کمرہ": "children's room", "راہداری": "hallway",
}


def _room_criterion(area: str, language: str) -> str:
    if language == "ur" and (gloss := _URDU_ROOM_GLOSSES.get(area)):
        return f"{area} / {gloss}"
    return area


def target_request(text: str, domain: str, candidates: list[Target], caller_area: str | None,
                   language: str | None = None) -> dict | None:
    if domain not in {"on_off", "temperature"} or not candidates:
        return None
    locale = get_locale(language or ("ru" if _russian(text) else "en"))
    if domain == "temperature":
        instructions = locale.target_prompts[0]
    elif all(t.kind == "light_group" for t in candidates):
        instructions = locale.target_prompts[1]
    elif all(t.kind in {"light_entity", "light_group"} for t in candidates):
        instructions = locale.target_prompts[2]
    else:
        instructions = locale.target_prompts[3]
    area = mentioned_area(text, {t.area for t in candidates if t.area})
    if caller_area and not area:
        instructions += (f" Комната вызова: {caller_area}." if locale.code == "ru"
                         else f" Caller area for unnamed room requests: {caller_area}.")
    if locale.code == "ur" and all(t.kind == "light_group" for t in candidates):
        instructions = "Choose the room explicitly mentioned by the user"
    none = ("другое" if locale.code == "ru" and all(t.kind == "light_group" for t in candidates)
            else locale.none_target)
    criteria = {}
    for target in candidates:
        label = (_room_criterion(target.area, locale.code)
                 if locale.code in {"ar", "bn", "ur"} and target.kind == "light_group" and target.area
                 else target.label)
        if locale.code == "ru" and any(item.kind == "light_entity" for item in candidates):
            if target.kind == "light_group" and target.area:
                label += f", общий свет {_russian_genitive(target.area)}"
            elif "верхн" in label.casefold():
                label += ", люстра, потолочный свет"
        if target.aliases:
            label += " / " + " / ".join(target.aliases)
        criteria[target.key] = label
    questions = {"target": {
            "type": "choice", "instructions": instructions,
            "criteria": {**criteria, "none": none},
        }}
    if locale.code == "ru" and all(target.kind == "light_group" for target in candidates):
        questions["target"]["criteria"] = {
            **{target.key: f"{target.label} / освещение {_russian_genitive(target.area)}"
               for target in candidates if target.area},
            "none": "другое",
        }
        questions["target_check"] = {
            "type": "choice", "instructions": "Какая цель указана пользователем?",
            "criteria": {**{target.key: f"{target.area}: свет, освещение"
                            for target in candidates if target.area}, "none": "другое"},
        }
    return _wire(text, questions, locale, target=True)


def selected_target(answers: dict, text: str, candidates: list[Target],
                    language: str | None = None,
                    thresholds: Thresholds | None = None) -> Target | None:
    gates = thresholds or Thresholds()
    first = answers.get("target")
    second = answers.get("target_check")
    raw = [item.get("choice") for item in (first, second) if isinstance(item, dict)]
    if not raw or len(set(raw)) > 1:
        return None
    key = raw[0]
    target = next((item for item in candidates if item.key == key), None)
    if target is None:
        return None
    normal_confidence = (max(gates.target_confidence, gates.temperature_confidence)
                         if target.kind == "temperature" else gates.target_confidence)
    normal_probability = (max(gates.target_probability, gates.temperature_probability)
                          if target.kind == "temperature" else gates.target_probability)
    valid = [item for item in (first, second) if item is not None and
             choice(item, normal_confidence, normal_probability) == key]
    if valid:
        return target
    named_area = mentioned_area(text, {item.area for item in candidates if item.area})
    soft_gates = gates.soft_dict()
    if target.kind == "temperature" and len(candidates) == 1:
        if named_area and target.area == named_area:
            return target if _soft_choice(first, gates.temperature_confidence,
                                          gates.temperature_probability) == key else None
        if not named_area:
            return target if _soft_choice(first, soft_gates["unnamed_temperature_confidence"],
                                          gates.temperature_probability) == key else None
    if not named_area or target.area != named_area:
        return None
    best = max((item for item in (first, second) if isinstance(item, dict)),
               key=lambda item: item.get("confidence", 0))
    if target.kind == "light_group" and second is not None:
        return target if _soft_choice(best, soft_gates["room_target_confidence"],
                                      soft_gates["room_target_probability"]) == key else None
    if target.kind == "light_entity" and is_specific_light_request(text, [target], named_area, language):
        return target if _soft_choice(best, soft_gates["fixture_target_confidence"],
                                      soft_gates["fixture_target_probability"]) == key else None
    return None


def detail_request(text: str, domain: str, language: str | None = None) -> dict | None:
    if domain != "on_off":
        return None
    locale = get_locale(language or ("ru" if _russian(text) else "en"))
    action = {"type": "choice", "instructions": locale.action_prompt,
              "criteria": dict(zip(("turn_on", "turn_off", "none"), locale.action_criteria))}
    check = {"type": "choice", "instructions": locale.action_check_prompt,
             "criteria": dict(zip(("turn_on", "turn_off", "none"), locale.state_criteria))}
    return _wire(text, {"action": action, "action_check": check}, locale)


def best_action(answers: dict, text: str, language: str | None = None,
                thresholds: Thresholds | None = None) -> str | None:
    gates = thresholds or Thresholds()
    options = [answers.get("action"), answers.get("action_check")]
    valid = [answer for answer in options if choice(answer, gates.action_confidence,
                                                   gates.action_probability) in {"turn_on", "turn_off"}]
    if not valid:
        return None
    selected = max(valid, key=lambda answer: answer["confidence"])
    action = choice(selected, gates.action_confidence, gates.action_probability)
    verb = explicit_action(text, language)
    if verb and action != verb:
        return None
    if not verb and len(valid) == 2 and choice(valid[0], gates.action_confidence, gates.action_probability) \
            != choice(valid[1], gates.action_confidence, gates.action_probability):
        return None
    return action


def valid_target(target: Target, text: str, caller_area: str | None, targets: list[Target],
                 language: str | None = None) -> bool:
    area = mentioned_area(text, {t.area for t in targets if t.area})
    if area and target.area != area:
        return False
    if target.kind == "all_lights":
        return whole_home_request(text, language) and not area
    if not area and is_light_request(text, language) and caller_area and target.area != caller_area:
        # An explicitly configured spoken target name overrides the caller room.
        if not any(name.casefold() in text.casefold() for name in (target.label, *target.aliases)):
            return False
    return True

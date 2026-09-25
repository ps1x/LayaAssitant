"""Build an allowlisted target catalog from Home Assistant's live registries."""

from collections import defaultdict

from homeassistant.helpers import area_registry, device_registry, entity_registry, label_registry

from .aliases import parse_area_overrides, parse_spoken_names
from .const import (
    CONF_CLIMATES, CONF_FANS, CONF_LIGHTS, CONF_SPOKEN_NAMES, CONF_SWITCHES, CONF_TEMPERATURE,
)
from .routing import Target, light_group_label


def caller_area(hass, device_id: str | None) -> str | None:
    if not device_id:
        return None
    device = device_registry.async_get(hass).async_get(device_id)
    area = area_registry.async_get(hass).async_get_area(device.area_id) if device and device.area_id else None
    return area.name if area else None


def build_targets(hass, options: dict, language: str = "en") -> list[Target]:
    """Rebuild per request so entity names and areas follow HA changes."""
    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)
    ar = area_registry.async_get(hass)
    lr = label_registry.async_get(hass)
    aliases = parse_spoken_names(options.get(CONF_SPOKEN_NAMES), language)
    selected_entities = {entity_id for field in (
        CONF_LIGHTS, CONF_SWITCHES, CONF_FANS, CONF_CLIMATES, CONF_TEMPERATURE
    ) for entity_id in options.get(field, [])}
    area_overrides = parse_area_overrides(options.get(CONF_SPOKEN_NAMES), selected_entities)
    entries = []
    allowed = {
        CONF_LIGHTS: {"light", "switch"}, CONF_SWITCHES: {"switch"},
        CONF_FANS: {"fan"}, CONF_CLIMATES: {"climate"},
        CONF_TEMPERATURE: {"sensor", "climate"},
    }
    for field, kind in (
        (CONF_LIGHTS, "light_entity"), (CONF_SWITCHES, "switch"),
        (CONF_FANS, "fan"), (CONF_CLIMATES, "climate"),
        (CONF_TEMPERATURE, "temperature"),
    ):
        for entity_id in options.get(field, []):
            if not isinstance(entity_id, str) or entity_id.split(".", 1)[0] not in allowed[field]:
                continue
            state = hass.states.get(entity_id)
            if state is None:
                continue
            reg = er.async_get(entity_id)
            device = dr.async_get(reg.device_id) if reg and reg.device_id else None
            area_id = (reg.area_id if reg else None) or (device.area_id if device else None)
            area = ar.async_get_area(area_id) if area_id else None
            name = aliases.get(entity_id) or (reg.name if reg and reg.name else None) or state.name or entity_id
            label_ids = set(reg.labels if reg else ()) | set(device.labels if device else ())
            label_names = sorted({label.name.strip() for label_id in label_ids
                                  if (label := lr.async_get_label(label_id)) and label.name.strip()
                                  and len(label.name) <= 80 and label.name.casefold() != name.casefold()})[:4]
            entries.append((entity_id, name, area_overrides.get(entity_id) or (area.name if area else None),
                            kind, tuple(label_names)))

    targets = []
    lighting_by_area = defaultdict(list)
    for i, (entity_id, name, area, kind, label_names) in enumerate(entries):
        if kind == "light_entity" and area:
            lighting_by_area[area].append(entity_id)
        # Every selected entity has its own target; its opaque key is scoped to this request.
        targets.append(Target(f"e{i}", name,
                              (entity_id,), area, kind, label_names))
    for i, (area, entities) in enumerate(sorted(lighting_by_area.items())):
        targets.append(Target(f"g{i}", aliases.get(f"area:{area}") or light_group_label(area, language),
                              tuple(sorted(entities)), area, "light_group"))
    all_lights = sorted({entity_id for entity_id, _, _, kind, _ in entries if kind == "light_entity"})
    if len(all_lights) > 1:
        targets.append(Target("all_lights", "All approved lights in the whole home",
                              tuple(all_lights), None, "all_lights"))
    return targets

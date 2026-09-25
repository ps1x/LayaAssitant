"""Optional user-provided spoken labels, without changing the entity allowlist."""

import json

from .locale import get_locale


def parse_spoken_names(value: str | None, language: str) -> dict[str, str]:
    """Accept flat labels and per-language overrides in a bounded JSON object."""
    raw = json.loads(value or "{}")
    if not isinstance(raw, dict) or len(raw) > 256:
        raise ValueError("spoken names must be a JSON object with at most 256 keys")
    labels = {}
    nested = {}
    for key, item in raw.items():
        if not isinstance(key, str) or not key or len(key) > 160:
            raise ValueError("invalid spoken name key")
        if isinstance(item, str):
            if not item.strip() or len(item) > 160:
                raise ValueError("spoken names must be 1-160 characters")
            labels[key] = item.strip()
        elif isinstance(item, dict):
            if len(item) > 256 or any(
                not isinstance(k, str) or not k or len(k) > 160
                or not isinstance(v, str) or not v.strip() or len(v) > 160
                for k, v in item.items()
            ):
                raise ValueError("invalid language-specific spoken names")
            nested[key] = {k: v.strip() for k, v in item.items()}
        else:
            raise ValueError("spoken name values must be strings or language maps")
    labels.update(nested.get("*", {}))
    labels.update(nested.get(get_locale(language).code, {}))
    return labels

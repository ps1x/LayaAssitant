"""Bounded, credential-free model diagnostics for opt-in speech and state."""

import math


def _score(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return round(float(value), 4) if 0 <= value <= 1 else None


def summarize_answers(answers: dict) -> dict[str, dict]:
    """Keep only the choice and probability fields used by routing."""
    summary = {}
    for question, answer in list(answers.items())[:8]:
        if not isinstance(question, str) or len(question) > 64 or not isinstance(answer, dict):
            continue
        probabilities = answer.get("probabilities")
        summary[question] = {
            "choice": answer.get("choice") if isinstance(answer.get("choice"), str)
                      and len(answer["choice"]) <= 64 else None,
            "confidence": _score(answer.get("confidence")),
            "probabilities": {
                key: score for key, raw in
                (list(probabilities.items())[:64] if isinstance(probabilities, dict) else ())
                if isinstance(key, str) and len(key) <= 64 and (score := _score(raw)) is not None
            },
        }
    return summary


def format_debug(trace: dict, metrics: dict) -> str:
    """Append human-readable diagnostics without raw requests or credentials."""
    parts = [f"DEBUG status={metrics.get('status', 'unknown')}"]
    if trace.get("reason"):
        parts[0] += f" reason={trace['reason']}"
    for stage, questions in trace.get("stages", {}).items():
        for name, answer in questions.items():
            scores = ", ".join(
                f"{key}={value:.4f}" for key, value in
                sorted(answer["probabilities"].items(), key=lambda item: (-item[1], item[0]))
            )
            confidence = answer["confidence"]
            parts.append(f"{stage}.{name}: choice={answer['choice']} confidence="
                         f"{confidence:.4f}" if confidence is not None else
                         f"{stage}.{name}: choice={answer['choice']} confidence=invalid")
            parts[-1] += f" probabilities=[{scores}]"
        parts.append(f"{stage}: accepted={trace.get('decisions', {}).get(stage)} "
                     f"time={metrics.get(stage + '_ms', 0)}ms")
    if candidates := trace.get("candidates"):
        selected = trace.get("decisions", {}).get("target")
        if not selected:
            selected = trace.get("stages", {}).get("target", {}).get("target", {}).get("choice")
        if selected in candidates:
            item = candidates[selected]
            parts.append(f"target {selected}={item['name']} ({'/'.join(item['entities'])})")
    thresholds = trace.get("thresholds", {})
    parts.append("thresholds: " + ", ".join(f"{key}={value:.2f}" for key, value in thresholds.items()))
    if soft := trace.get("soft_thresholds"):
        parts.append("anchored thresholds: " + ", ".join(
            f"{key}={value:.2f}" for key, value in soft.items()
        ))
    parts.append(f"total={metrics.get('total_ms', 0)}ms")
    return "\n".join(parts)

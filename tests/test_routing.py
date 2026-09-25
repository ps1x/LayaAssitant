"""Pure routing checks without importing Home Assistant."""

import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "laya_assistant"
package = types.ModuleType("laya_assistant")
package.__path__ = [str(ROOT)]
sys.modules["laya_assistant"] = package
for name in ("const", "routing"):
    spec = importlib.util.spec_from_file_location(f"laya_assistant.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from laya_assistant.routing import (  # noqa: E402
    Target, best_action, choice, domain_request, explicit_action,
    light_group_label, mentioned_area, selected_domain, selected_target,
    target_candidates, valid_target,
)
from laya_assistant.locale import LOCALES, get_locale  # noqa: E402
from laya_assistant.aliases import parse_area_overrides, parse_spoken_names  # noqa: E402


def answer(value, confidence=0.95, probability=0.96):
    return {"type": "choice", "choice": value, "confidence": confidence,
            "probabilities": {value: probability}}


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.targets = [
            Target("e0", "Верхний свет в детской", ("switch.kids_top",), "Детская", "light_entity"),
            Target("e1", "Свет над столом в детской", ("switch.kids_desk",), "Детская", "light_entity"),
            Target("e2", "Свет кухни", ("light.kitchen",), "Кухня", "light_entity"),
            Target("g0", "Lights in Детская", ("switch.kids_top", "switch.kids_desk"), "Детская", "light_group"),
            Target("g1", "Lights in Кухня", ("light.kitchen",), "Кухня", "light_group"),
            Target("e3", "Приточка", ("fan.fresh_air",), "Детская", "fan"),
            Target("e4", "Улица", ("sensor.outside",), "Улица", "temperature"),
        ]

    def test_choice_rejects_low_and_nonfinite_scores(self):
        self.assertEqual(choice(answer("on_off")), "on_off")
        self.assertIsNone(choice(answer("on_off", confidence=0.79)))
        self.assertIsNone(choice(answer("on_off", probability=float("nan"))))
        self.assertIsNone(choice({"type": "choice", "choice": "x", "confidence": True,
                                  "probabilities": {"x": 1.0}}))

    def test_dynamic_room_and_light_candidates(self):
        self.assertEqual(mentioned_area("в детской", {"Детская", "Кухня"}), "Детская")
        self.assertEqual(mentioned_area("на кухне", {"Детская", "Кухня"}), "Кухня")
        generic = target_candidates("включи свет в детской", "on_off", self.targets, "Детская")
        self.assertEqual({target.key for target in generic}, {"g0", "g1"})
        specific = target_candidates("включи верхний свет в детской", "on_off", self.targets, "Детская")
        self.assertEqual({target.key for target in specific}, {"g0", "e0", "e1"})
        self.assertFalse(valid_target(self.targets[4], "включи свет в детской", "Детская", self.targets))

    def test_action_is_model_choice_with_text_veto(self):
        self.assertEqual(best_action({"action": answer("turn_on", 0.40),
                                      "action_check": answer("turn_off", 0.98)},
                                     "выключи свет"), "turn_off")
        self.assertIsNone(best_action({"action": answer("turn_on", 0.98),
                                       "action_check": answer("turn_off", 0.70)},
                                      "выключи свет"))
        self.assertEqual(explicit_action("свет в детской включи"), "turn_on")

    def test_soft_gates_need_explicit_text_anchors(self):
        self.assertEqual(selected_domain(answer("on_off", 0.70, 0.90),
                                         "зажги свет в детской", "ru"), "on_off")
        self.assertIsNone(selected_domain(answer("on_off", 0.70, 0.90),
                                          "свет в детской", "ru"))
        candidate = self.targets[3]
        answers = {"target": answer("g0", 0.69, 0.91),
                   "target_check": answer("g0", 0.46, 0.78)}
        self.assertEqual(selected_target(answers, "включи освещение в детской",
                                         [candidate, self.targets[4]], "ru"), candidate)
        self.assertIsNone(selected_target(answers, "включи освещение",
                                          [candidate, self.targets[4]], "ru"))

    def test_domain_has_no_entity_id(self):
        request = domain_request("включи свет в детской")
        self.assertEqual(set(request["questions"]), {"domain"})
        self.assertNotIn("switch.kids_top", str(request))

    def test_automatic_language_and_english_fallback(self):
        self.assertEqual(len(LOCALES), 12)
        self.assertEqual(get_locale("pt-BR").code, "pt")
        self.assertEqual(get_locale("zh-Hans").code, "zh")
        self.assertEqual(get_locale("de-DE").code, "de")
        self.assertEqual(get_locale("ja").code, "en")
        for code, locale in LOCALES.items():
            self.assertEqual(len(locale.replies), 10, code)
            self.assertTrue(domain_request("test", code)["questions"]["domain"]["instructions"])
            self.assertTrue((ROOT / "translations" / f"{code}.json").is_file(), code)
        self.assertEqual(light_group_label("Детская", "ru"), "свет в детской")
        self.assertEqual(light_group_label("Bedroom", "de"), "Licht in Bedroom")

    def test_action_words_in_supported_languages(self):
        examples = {
            "en": ("turn on light", "turn off light"),
            "zh": ("打开灯", "关闭灯"),
            "hi": ("लाइट चालू", "लाइट बंद"),
            "es": ("enciende la luz", "apaga la luz"),
            "ar": ("شغل الضوء", "أطفئ الضوء"),
            "fr": ("allume la lumière", "éteins la lumière"),
            "bn": ("আলো চালু", "আলো বন্ধ"),
            "pt": ("ligue a luz", "desligue a luz"),
            "id": ("nyalakan lampu", "matikan lampu"),
            "ur": ("بتی چلاؤ", "بتی بند"),
            "ru": ("включи свет", "выключи свет"),
            "de": ("schalte ein", "schalte aus"),
        }
        for code, (on, off) in examples.items():
            self.assertEqual(explicit_action(on, code), "turn_on", code)
            self.assertEqual(explicit_action(off, code), "turn_off", code)

    def test_spoken_names_are_localized_and_bounded(self):
        raw = json.dumps({"area:Детская": "lights in the children's room",
                          "ru": {"area:Детская": "свет в детской"}}, ensure_ascii=False)
        self.assertEqual(parse_spoken_names(raw, "ru-RU")["area:Детская"], "свет в детской")
        self.assertEqual(parse_spoken_names(raw, "en")["area:Детская"], "lights in the children's room")
        with self.assertRaises(ValueError):
            parse_spoken_names('{"area:Детская": ["switch.any"]}', "ru")

    def test_explicit_area_assignments_and_temperature_soft_gate(self):
        raw = json.dumps({"areas": {"switch.kids_top": "Детская"}}, ensure_ascii=False)
        self.assertEqual(parse_area_overrides(raw, {"switch.kids_top"}),
                         {"switch.kids_top": "Детская"})
        with self.assertRaises(ValueError):
            parse_area_overrides(raw, {"switch.other"})
        sensor = Target("e0", "Температура в гостиной", ("sensor.living",),
                        "Гостиная", "temperature")
        self.assertEqual(selected_target({"target": answer("e0", 0.367, 0.8405)},
                                         "какая температура в гостинной", [sensor], "ru"), sensor)
        self.assertIsNone(selected_target({"target": answer("e0", 0.29, 0.92)},
                                          "какая температура в гостиной", [sensor], "ru"))

    def test_unassigned_lights_do_not_become_an_implicit_room_group(self):
        unassigned = [Target("e0", "Desk lamp", ("light.desk",), None, "light_entity")]
        self.assertEqual(target_candidates("turn on the lights in bedroom", "on_off",
                                           unassigned, None, "en"), [])


if __name__ == "__main__":
    unittest.main()

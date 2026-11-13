import ast
import json
import re
import unittest
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment


BLUEPRINT_PATH = (
    Path(__file__).parents[1]
    / "Awtrix NFL Team Scoreboard"
    / "awtrix_nfl_team_scoreboard.yaml"
)


class BlueprintLoader(yaml.SafeLoader):
    pass


BlueprintLoader.add_constructor("!input", lambda loader, node: loader.construct_scalar(node))


class NFLTeamColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with BLUEPRINT_PATH.open(encoding="utf-8") as blueprint_file:
            cls.blueprint = yaml.load(blueprint_file, Loader=BlueprintLoader)

        cls.environment = Environment()
        cls.environment.tests["match"] = lambda value, pattern: re.match(pattern, value) is not None
        cls.environment.tests["search"] = lambda value, pattern: re.search(pattern, value) is not None
        cls.environment.filters["regex_replace"] = lambda value, pattern, replacement="": re.sub(
            pattern, replacement, value
        )
        cls.environment.filters["int"] = cls.ha_int
        cls.environment.globals.update(
            {
                "now": lambda: datetime(2026, 11, 12, 19, 30),
                "states": lambda entity: "test_awtrix",
                "device_entities": lambda device_id: [f"sensor.{device_id}_device_topic"],
            }
        )
        cls.payload_environment = Environment()
        cls.payload_environment.filters["regex_replace"] = cls.environment.filters["regex_replace"]

    @staticmethod
    def ha_int(value, default=..., base=10):
        try:
            if isinstance(value, str):
                return int(value, base)
            return int(value)
        except (TypeError, ValueError):
            if default is ...:
                raise ValueError(f"int got invalid input {value!r} when no default was specified")
            return default

    @staticmethod
    def parse_template_result(rendered):
        rendered = rendered.strip()
        if rendered.startswith(('"', "'")):
            return rendered
        try:
            return ast.literal_eval(rendered)
        except (ValueError, SyntaxError):
            return rendered

    def render_scoreboard(
        self,
        team_color="#FFFFFF",
        opponent_color="#EEEEEE",
        display_mode="my_team_left",
        team_homeaway="away",
        team_abbr="SEA",
        opponent_abbr="NYJ",
        team_score=7,
        opponent_score=3,
        additional_attributes=None,
        missing_attributes=(),
        input_overrides=None,
    ):
        def color_attribute(color, accent):
            if color is None or isinstance(color, (list, tuple, int)):
                return color
            return [color, accent]

        attributes = {
            "team_abbr": team_abbr,
            "opponent_abbr": opponent_abbr,
            "team_homeaway": team_homeaway,
            "team_colors": color_attribute(team_color, "#FDFDFD"),
            "opponent_colors": color_attribute(opponent_color, "#FEDCBA"),
            "team_score": team_score,
            "opponent_score": opponent_score,
            "clock": "7:30 PM",
            "kickoff_in": "Soon",
        }
        for key, value in (additional_attributes or {}).items():
            if value is missing:
                attributes.pop(key, None)
            else:
                attributes[key] = value
        for key in missing_attributes:
            attributes.pop(key, None)

        inputs = {
            "awtrix": ["test_device"],
            "appname": "sportsteamscore",
            "my_sensor": "sensor.test",
            "my_timer": "timer.test",
            "display_mode": display_mode,
            "message_duration": 15,
            "message_lifetime": 1,
            "my_timer_1st_2nd_intermission": 1030,
            "my_timer_overtime_intermission": 0,
            "score_leading_zero": True,
        }
        inputs.update(input_overrides or {})
        context = {
            "state_attr": lambda entity, attribute: attributes.get(attribute),
        }
        variables = self.blueprint["variables"]
        payload_names = {name for name in variables if name.startswith("payload_")}
        color_names = {
            "left_team_colors_raw_0",
            "left_team_colors_1",
            "right_team_colors_raw_0",
            "right_team_colors_1",
            "team_colors_0",
            "team_colors_1",
            "opponent_colors_0",
            "opponent_colors_1",
        }
        for name, value in variables.items():
            if isinstance(value, str) and value in inputs:
                context[name] = inputs[value]
            elif isinstance(value, str) and ("{{" in value or "{%" in value):
                environment = self.payload_environment if name in payload_names else self.environment
                rendered = environment.from_string(value).render(context)
                if name in payload_names:
                    context[name] = json.loads(rendered)
                elif name in color_names and isinstance(rendered, str):
                    context[name] = rendered.strip()
                else:
                    context[name] = self.parse_template_result(rendered)
            else:
                context[name] = value

        payloads = {
            name: context[name]
            for name in payload_names
            if name.startswith("payload_game_") or name.endswith("_quarter")
        }
        return context, payloads

    def assert_payload_colors(self, context, payloads):
        expected_backgrounds = [context["left_team_colors_0"], context["right_team_colors_0"]]
        expected_accents = [context["left_team_colors_1"], context["right_team_colors_1"]]

        for payload in payloads.values():
            draw = payload["draw"]
            self.assertEqual([draw[0]["df"][4], draw[1]["df"][4]], expected_backgrounds)
            self.assertEqual(
                [item["dl"][4] for item in draw[2:6]],
                [expected_accents[0], expected_accents[0], expected_accents[1], expected_accents[1]],
            )

    def assert_payload_scores(self, payload, expected):
        scores = [item["dt"][2] for item in payload["draw"] if "dt" in item]
        self.assertEqual(scores, expected)

    def assert_all_payload_scores(self, payloads, expected):
        for name, payload in payloads.items():
            if name != "payload_game_prestart":
                with self.subTest(payload=name):
                    self.assert_payload_scores(payload, expected)

    def test_white_and_light_grey_backgrounds_are_darkened_without_changing_accents(self):
        context, payloads = self.render_scoreboard("#FFFFFF", "#EEEEEE")

        self.assertEqual(context["left_team_colors_0"], "#707070")
        self.assertEqual(context["right_team_colors_0"], "#707070")
        self.assertEqual(context["left_team_colors_1"], "#FDFDFD")
        self.assertEqual(context["right_team_colors_1"], "#FEDCBA")
        self.assert_payload_colors(context, payloads)

    def test_tinted_neutral_colors_are_scaled_while_preserving_their_tint(self):
        context, payloads = self.render_scoreboard("#F4F2EF", "#E8E8F0")

        self.assertEqual(context["left_team_colors_0"], "#706f6d")
        self.assertEqual(context["right_team_colors_0"], "#6c6c70")
        self.assert_payload_colors(context, payloads)

    def test_colored_and_darker_grey_backgrounds_are_unchanged(self):
        context, payloads = self.render_scoreboard("#D50A0A", "#808080")

        self.assertEqual(context["left_team_colors_0"], "#D50A0A")
        self.assertEqual(context["right_team_colors_0"], "#808080")
        self.assert_payload_colors(context, payloads)

    def test_home_team_right_mode_swaps_before_darkening(self):
        context, payloads = self.render_scoreboard(
            "#FFFFFF", "#004488", display_mode="home_team_right", team_homeaway="home"
        )

        self.assertEqual(context["left_team_colors_0"], "#004488")
        self.assertEqual(context["right_team_colors_0"], "#707070")
        self.assert_payload_colors(context, payloads)

    def test_home_team_right_mode_keeps_away_team_on_left(self):
        context, payloads = self.render_scoreboard(
            "#FFFFFF", "#004488", display_mode="home_team_right", team_homeaway="away"
        )

        self.assertEqual(context["left_team_colors_0"], "#707070")
        self.assertEqual(context["right_team_colors_0"], "#004488")
        self.assert_payload_colors(context, payloads)

    def test_lightness_and_neutrality_boundaries(self):
        for color, expected in (
            ("#d0d0d0", "#707070"),
            ("#cfcfcf", "#cfcfcf"),
            ("#ffe7e7", "#706565"),
            ("#ffe6e6", "#ffe6e6"),
        ):
            with self.subTest(color=color):
                context, payloads = self.render_scoreboard(color, "#004488")
                self.assertEqual(context["left_team_colors_0"], expected)
                self.assert_payload_colors(context, payloads)

    def test_unrecognized_colors_pass_through(self):
        for color in ("#fff", "#GGGGGG", "FFFFFF", "#FFFFFFFF", "lightgrey"):
            with self.subTest(color=color):
                context, payloads = self.render_scoreboard(color, "#004488")
                self.assertEqual(context["left_team_colors_0"], color)
                self.assert_payload_colors(context, payloads)

    def test_team_override_is_preserved_when_swapped(self):
        context, payloads = self.render_scoreboard(
            "#FFFFFF", "#EEEEEE", display_mode="home_team_right", team_homeaway="home",
            team_abbr="CAN",
        )

        self.assertEqual(context["left_team_colors_0"], "#707070")
        self.assertEqual(context["right_team_colors_0"], "#D80621")
        self.assertEqual(context["right_team_colors_1"], "#FFFFFF")
        self.assert_payload_colors(context, payloads)

    def test_missing_attributes_use_safe_colors_zero_scores_and_empty_pregame_text(self):
        context, payloads = self.render_scoreboard(
            missing_attributes=(
                "team_colors",
                "opponent_colors",
                "team_score",
                "opponent_score",
                "clock",
                "kickoff_in",
            )
        )

        self.assertEqual(context["team_colors_safe"], ["#000000", "#FFFFFF"])
        self.assertEqual(context["opponent_colors_safe"], ["#000000", "#FFFFFF"])
        self.assertEqual(context["pregame_notice"], "")
        self.assertEqual(context["game_clock"], "")
        self.assertNotIn("None", payloads["payload_game_prestart"]["text"])
        self.assertEqual(context["left_team_score"], 0)
        self.assertEqual(context["right_team_score"], 0)
        self.assert_all_payload_scores(payloads, ["00", "00"])
        self.assert_payload_colors(context, payloads)

    def test_integer_and_none_color_attributes_and_invalid_scores_are_safe_when_swapped(self):
        context, payloads = self.render_scoreboard(
            team_color=42,
            opponent_color=None,
            display_mode="home_team_right",
            team_homeaway="home",
            team_score="not-a-score",
            opponent_score=None,
            input_overrides={"score_leading_zero": False},
        )

        self.assertEqual(context["team_colors_safe"], ["#000000", "#FFFFFF"])
        self.assertEqual(context["opponent_colors_safe"], ["#000000", "#FFFFFF"])
        self.assertEqual(context["left_team_score"], 0)
        self.assertEqual(context["right_team_score"], 0)
        self.assert_all_payload_scores(payloads, ["0", "0"])
        self.assert_payload_colors(context, payloads)

    def test_scores_are_numeric_and_formatted_in_all_game_payloads(self):
        for score, expected_position in ((0, 11), (7, 11), (10, 7), (-1, 7)):
            for leading_zero in (True, False):
                with self.subTest(score=score, leading_zero=leading_zero):
                    context, payloads = self.render_scoreboard(
                        team_score=score,
                        opponent_score=score,
                        input_overrides={"score_leading_zero": leading_zero},
                    )

                    self.assertIsInstance(context["left_team_score"], int)
                    self.assertIsInstance(context["right_team_score"], int)
                    self.assertEqual(context["left_team_score_x"], expected_position)
                    formatted_score = (
                        f"0{score}" if leading_zero and 0 <= score < 10 else str(score)
                    )
                    self.assert_all_payload_scores(
                        payloads, [formatted_score, formatted_score]
                    )

    def test_scores_follow_display_mode_when_teams_are_swapped(self):
        context, payloads = self.render_scoreboard(
            team_score=7,
            opponent_score=12,
            display_mode="home_team_right",
            team_homeaway="home",
        )

        self.assertEqual(context["left_team_score"], 12)
        self.assertEqual(context["right_team_score"], 7)
        self.assertEqual(context["left_team_score_x"], 7)
        self.assert_all_payload_scores(payloads, ["12", "07"])
        self.assert_payload_colors(context, payloads)

    def test_short_color_arrays_keep_valid_values_and_fill_missing_entries(self):
        context, payloads = self.render_scoreboard(
            team_color=["#123456"],
            opponent_color=["#AABBCC", 7],
        )

        self.assertEqual(context["team_colors_safe"], ["#123456", "#FFFFFF"])
        self.assertEqual(context["opponent_colors_safe"], ["#AABBCC", "#FFFFFF"])
        self.assertEqual(context["left_team_colors_0"], "#123456")
        self.assertEqual(context["right_team_colors_0"], "#AABBCC")
        self.assertEqual(context["left_team_colors_1"], "#FFFFFF")
        self.assertEqual(context["right_team_colors_1"], "#FFFFFF")
        self.assert_payload_colors(context, payloads)


if __name__ == "__main__":
    unittest.main()
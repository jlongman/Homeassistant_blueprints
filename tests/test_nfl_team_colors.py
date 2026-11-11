import json
import re
import unittest
from pathlib import Path

import yaml
from jinja2 import Environment
from jinja2.nativetypes import NativeEnvironment


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

        cls.environment = NativeEnvironment()
        cls.environment.tests["match"] = lambda value, pattern: re.match(pattern, value) is not None
        cls.environment.filters["regex_replace"] = lambda value, pattern, replacement="": re.sub(
            pattern, replacement, value
        )
        cls.payload_environment = Environment()
        cls.payload_environment.filters["regex_replace"] = cls.environment.filters["regex_replace"]

    def render_scoreboard(
        self, team_color, opponent_color, display_mode="team_left", team_homeaway="away",
        team_abbr="SEA", opponent_abbr="NYJ",
    ):
        attributes = {
            "team_abbr": team_abbr,
            "opponent_abbr": opponent_abbr,
            "team_homeaway": team_homeaway,
            "team_colors": [team_color, "#FDFDFD"],
            "opponent_colors": [opponent_color, "#FEDCBA"],
            "team_score": 7,
            "opponent_score": 3,
            "clock": "7:30 PM",
            "kickoff_in": "Soon",
        }
        context = {
            "my_sensor": "sensor.test",
            "display_mode": display_mode,
            "state_attr": lambda entity, attribute: attributes[attribute],
        }
        variables = self.blueprint["variables"]
        context["is_swapped"] = self.environment.from_string(variables["is_swapped"]).render(context)

        for name in (
            "left_team_colors_raw_0",
            "left_team_colors_1",
            "right_team_colors_raw_0",
            "right_team_colors_1",
        ):
            context[name] = self.environment.from_string(variables[name]).render(context).strip()

        context["scoreboard_background_colors"] = self.environment.from_string(
            variables["scoreboard_background_colors"]
        ).render(context)
        for name in ("left_team_colors_0", "right_team_colors_0"):
            context[name] = self.environment.from_string(variables[name]).render(context)

        context.update(
            {
                "first_quarter": variables["first_quarter"],
                "second_quarter": variables["second_quarter"],
                "third_quarter": variables["third_quarter"],
                "fourth_quarter": variables["fourth_quarter"],
                "game_clock": "7:30 PM",
                "date_stripper": "",
                "timezone_regex": r" ?[A-Z][SD]T",
                "pregame_notice": "Soon",
                "message_duration": 15,
                "left_team_score_x": 11,
                "right_team_score_x": 18,
                "left_team_score": "7",
                "right_team_score": "3",
            }
        )
        payload_names = (
            "payload_game_prestart",
            "payload_game_start",
            "payload_second_quarter",
            "payload_third_quarter",
            "payload_fourth_quarter",
        )
        payloads = {
            name: json.loads(self.payload_environment.from_string(variables[name]).render(context))
            for name in payload_names
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


if __name__ == "__main__":
    unittest.main()
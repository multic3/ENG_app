import re
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from pydantic import ValidationError

from app import database, main
from app.progression import (
    xp_threshold_for_level,
)


class GameFlowTests(unittest.TestCase):

    def setUp(self):
        self.original_db_path = database.DB_PATH
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )
        database.DB_PATH = (
            Path(self.temp_directory.name)
            / "test.db"
        )
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.temp_directory.cleanup()

    def unlock_green_valley_boss(self):
        for level_id in range(1, 10):
            main.finish_level(
                level_id,
                database.DEFAULT_PLAYER_ID,
            )

    def unlock_sunny_beach_boss(self):
        self.unlock_green_valley_boss()
        main.finish_boss(
            10,
            main.BossResultRequest(
                correct_answers=5,
                total_answers=5,
            ),
            database.DEFAULT_PLAYER_ID,
        )

        for level_id in range(11, 20):
            main.finish_level(
                level_id,
                database.DEFAULT_PLAYER_ID,
            )

    def test_normal_level_unlocks_next_level(self):
        result = main.finish_level(
            1,
            database.DEFAULT_PLAYER_ID,
        )

        self.assertEqual(
            result["progress"]["current_level"],
            2,
        )
        self.assertEqual(
            result["next_level"],
            2,
        )

    def test_locked_boss_cannot_be_submitted(self):
        with self.assertRaises(HTTPException) as raised:
            main.finish_boss(
                10,
                main.BossResultRequest(
                    correct_answers=5,
                    total_answers=5,
                ),
                database.DEFAULT_PLAYER_ID,
            )

        self.assertEqual(
            raised.exception.status_code,
            403,
        )

    def test_boss_cannot_use_normal_completion(self):
        self.unlock_green_valley_boss()

        with self.assertRaises(HTTPException) as raised:
            main.finish_level(
                10,
                database.DEFAULT_PLAYER_ID,
            )

        self.assertEqual(
            raised.exception.status_code,
            400,
        )

    def test_invalid_boss_scores_are_rejected(self):
        with self.assertRaises(ValidationError):
            main.BossResultRequest(
                correct_answers=0,
                total_answers=0,
            )

        self.unlock_green_valley_boss()

        with self.assertRaises(HTTPException) as raised:
            main.finish_boss(
                10,
                main.BossResultRequest(
                    correct_answers=2,
                    total_answers=1,
                ),
                database.DEFAULT_PLAYER_ID,
            )

        self.assertEqual(
            raised.exception.status_code,
            422,
        )

    def test_green_valley_boss_unlocks_sunny_beach(self):
        self.unlock_green_valley_boss()

        result = main.finish_boss(
            10,
            main.BossResultRequest(
                correct_answers=5,
                total_answers=5,
            ),
            database.DEFAULT_PLAYER_ID,
        )

        self.assertEqual(
            result["next_level"],
            11,
        )
        self.assertEqual(
            result["progress"]["current_level"],
            11,
        )
        self.assertIn(
            10,
            result["progress"]["completed_levels"],
        )

    def test_existing_boss_completion_unlocks_new_content(self):
        database.complete_level(
            10,
            0,
            None,
        )

        self.assertEqual(
            database.get_progress()["current_level"],
            10,
        )

        database.advance_past_completed_levels(20)

        self.assertEqual(
            database.get_progress()["current_level"],
            11,
        )

    def test_last_available_level_does_not_unlock_missing_content(self):
        self.unlock_sunny_beach_boss()

        result = main.finish_boss(
            20,
            main.BossResultRequest(
                correct_answers=8,
                total_answers=8,
            ),
            database.DEFAULT_PLAYER_ID,
        )

        self.assertIsNone(result["next_level"])
        self.assertEqual(
            result["progress"]["current_level"],
            20,
        )
        self.assertIn(
            20,
            result["progress"]["completed_levels"],
        )

    def test_hearts_never_drop_below_zero(self):
        for _ in range(database.MAX_HEARTS):
            self.assertTrue(
                database.spend_heart()
            )

        self.assertFalse(
            database.spend_heart()
        )
        self.assertEqual(
            database.get_progress()["hearts"],
            0,
        )

    def test_progress_is_clamped_to_available_content(self):
        database.complete_level(
            10,
            0,
            11,
        )

        database.clamp_current_level(10)

        self.assertEqual(
            database.get_progress()["current_level"],
            10,
        )

    def test_existing_progress_gets_minimum_xp_for_level(self):
        database.complete_level(
            4,
            1,
            5,
        )

        database.ensure_minimum_xp_for_level(
            5
        )
        progress = database.get_progress()

        self.assertEqual(
            progress["xp"],
            xp_threshold_for_level(5),
        )
        self.assertEqual(
            progress["player_level"],
            5,
        )

    def test_game_uses_requested_player_name(self):
        game = main.get_game(
            database.DEFAULT_PLAYER_ID
        )

        self.assertEqual(
            game["player"]["name"],
            "Anya is a princess",
        )

    def test_players_have_independent_progress(self):
        database.upsert_player(
            "tester_2",
            "Second Tester",
        )

        main.finish_level(
            1,
            database.DEFAULT_PLAYER_ID,
        )

        anya_progress = database.get_progress(
            database.DEFAULT_PLAYER_ID
        )
        tester_progress = database.get_progress(
            "tester_2"
        )

        self.assertEqual(
            anya_progress["current_level"],
            2,
        )
        self.assertEqual(
            tester_progress["current_level"],
            1,
        )
        self.assertEqual(
            tester_progress["completed_levels"],
            [],
        )

        main.finish_level(1, "tester_2")

        self.assertIn(
            1,
            database.get_progress(
                "tester_2"
            )["completed_levels"],
        )

    def test_present_continuous_translation_accepts_optional_now(self):
        level = main.find_level(
            main.GAME_DATA,
            9,
        )
        translation = level["steps"][0]

        self.assertEqual(
            translation["answer"],
            "The cat is sleeping now.",
        )
        self.assertIn(
            "The cat is sleeping.",
            translation["accepted_answers"],
        )

    def test_fill_gap_steps_include_sentence_and_verb_cue(self):
        for level_id in (2, 7, 10, 12, 15, 16, 20):
            level = main.find_level(
                main.GAME_DATA,
                level_id,
            )
            text_steps = [
                step
                for step in level["steps"]
                if step["type"] == "text"
            ]

            for step in text_steps:
                self.assertIn("___", step["sentence"])
                self.assertIn("form of", step["question"])

    def test_available_levels_are_contiguous_and_documented(self):
        levels = [
            level
            for location in main.GAME_DATA["locations"]
            for level in location.get("levels", [])
        ]

        self.assertEqual(
            [level["id"] for level in levels],
            list(range(1, 21)),
        )

        for level in levels:
            self.assertIn("grammar_help", level)
            self.assertGreaterEqual(len(level["steps"]), 1)

        self.assertTrue(levels[9]["boss"])
        self.assertTrue(levels[19]["boss"])

    def test_second_location_is_sunny_beach(self):
        location = main.GAME_DATA["locations"][1]

        self.assertEqual(location["name"], "Sunny Beach")
        self.assertEqual(location["theme"], "beach")
        self.assertEqual(len(location["levels"]), 10)

    def test_english_prompts_have_russian_translations(self):
        for location in main.GAME_DATA["locations"]:
            for level in location.get("levels", []):
                for step in level["steps"]:
                    if not re.search(
                        r"[А-Яа-яЁё]",
                        step["question"],
                    ):
                        self.assertTrue(
                            step.get("question_translation"),
                            f"Missing question translation in level {level['id']}",
                        )

                    if step.get("sentence"):
                        self.assertTrue(
                            step.get("sentence_translation"),
                            f"Missing sentence translation in level {level['id']}",
                        )


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
import sqlite3
from pathlib import Path

from fastapi import HTTPException

from app import database, main


class GameFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.temp_directory.name) / "test.db"
        database.init_db()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_manifest_and_authored_content_counts(self):
        self.assertEqual(len(main.GAME_DATA["locations"]), 100)
        authored_points = [
            point
            for location in main.GAME_DATA["locations"]
            for point in location.get("points", [])
        ]
        exercises = [
            exercise
            for point in authored_points
            for exercise in point["exercises"]
        ]
        self.assertEqual([point["id"] for point in authored_points], list(range(1, 101)))
        self.assertEqual(len(exercises), 500)
        self.assertEqual(len({item["id"] for item in exercises}), 500)
        self.assertEqual(len({item["prompt"] for item in exercises}), 500)

    def test_cefr_ranges_and_planned_locations(self):
        locations = main.GAME_DATA["locations"]
        self.assertTrue(all(item["cefr"] == "A2" for item in locations[:20]))
        self.assertTrue(all(item["cefr"] == "B1" for item in locations[20:60]))
        self.assertTrue(all(item["cefr"] == "B2" for item in locations[60:]))
        self.assertTrue(all(item["content_status"] == "planned" for item in locations[2:]))
        self.assertTrue(all(not item["points"] for item in locations[2:]))

    def test_every_point_has_five_exercises_and_four_types(self):
        required = {"multiple_choice", "fill_blank", "listening", "speech"}
        for location in main.GAME_DATA["locations"][:2]:
            self.assertEqual(len(location["points"]), 50)
            for point in location["points"]:
                types = [item["type"] for item in point["exercises"]]
                self.assertEqual(len(types), 5)
                self.assertEqual(set(types), required)
                self.assertFalse(any(left == right for left, right in zip(types, types[1:])))

    def test_normal_point_unlocks_next_and_records_delayed_review(self):
        attempt = main.ExerciseAttemptRequest(
            exercise_id="L001-P01-E1",
            correct=False,
            grammar_tags=["to_be"],
        )
        result = main.finish_level(
            1,
            database.DEFAULT_PLAYER_ID,
            main.CompletionRequest(attempts=[attempt]),
        )
        self.assertEqual(result["progress"]["current_level"], 2)
        self.assertEqual(main.due_review_queue(3, database.DEFAULT_PLAYER_ID)["reviews"], [])
        due = main.due_review_queue(4, database.DEFAULT_PLAYER_ID)["reviews"]
        self.assertEqual(due[0]["source_exercise_id"], "L001-P01-E1")

    def test_boss_is_every_fiftieth_point(self):
        with self.assertRaises(HTTPException) as raised:
            main.finish_level(50, database.DEFAULT_PLAYER_ID)
        self.assertEqual(raised.exception.status_code, 403)
        for point_id in range(1, 50):
            main.finish_level(point_id, database.DEFAULT_PLAYER_ID)
        result = main.finish_boss(
            50,
            main.BossResultRequest(correct_answers=5, total_answers=5),
            database.DEFAULT_PLAYER_ID,
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["next_level"], 51)

    def test_second_location_keeps_beach_visual_theme(self):
        location = main.GAME_DATA["locations"][1]
        self.assertEqual(location["theme"], "beach")
        self.assertEqual(location["id"], 2)
        self.assertEqual(location["points"][0]["id"], 51)

    def test_players_have_independent_progress(self):
        database.upsert_player("second_player", "Second")
        main.finish_level(1, database.DEFAULT_PLAYER_ID)
        self.assertEqual(database.get_progress(database.DEFAULT_PLAYER_ID)["current_level"], 2)
        self.assertEqual(database.get_progress("second_player")["current_level"], 1)

    def test_client_point_has_canonical_and_compatibility_views(self):
        response = main.get_level(1, database.DEFAULT_PLAYER_ID)
        self.assertEqual(len(response["point"]["exercises"]), 5)
        self.assertEqual(len(response["level"]["steps"]), 5)
        self.assertIn(response["point"]["exercises"][0]["type"], {
            "multiple_choice", "fill_blank", "listening", "speech"
        })
        for step in response["level"]["steps"]:
            if step["type"] in {"choice", "listening"}:
                self.assertIsInstance(step["answer"], int)
                canonical_answer = step["correct_answer"]
                self.assertEqual(step["options"][step["answer"]], canonical_answer)

    def test_speech_tasks_are_honest_about_assessment(self):
        speech_tasks = [
            exercise
            for location in main.GAME_DATA["locations"][:2]
            for point in location["points"]
            for exercise in point["exercises"]
            if exercise["type"] == "speech"
        ]
        self.assertGreater(len(speech_tasks), 0)
        for task in speech_tasks:
            self.assertIn(task["mode"], {"speech_repeat", "speech_response"})
            self.assertFalse(task["speech_settings"]["pronunciation_assessed"])
            self.assertTrue(task["accepted_answers"])

    def test_old_ten_point_progress_is_migrated_without_reset(self):
        legacy_path = Path(self.temp_directory.name) / "legacy.db"
        connection = sqlite3.connect(legacy_path)
        connection.execute(
            "CREATE TABLE player_progress (id INTEGER PRIMARY KEY, current_level INTEGER, xp INTEGER)"
        )
        connection.execute(
            "CREATE TABLE completed_levels (level_id INTEGER PRIMARY KEY, completed_at DATETIME)"
        )
        connection.execute("INSERT INTO player_progress VALUES (1, 11, 321)")
        connection.executemany(
            "INSERT INTO completed_levels VALUES (?, CURRENT_TIMESTAMP)",
            [(point_id,) for point_id in range(1, 11)],
        )
        connection.commit()
        connection.close()

        database.DB_PATH = legacy_path
        database.init_db()
        progress = database.get_progress()
        self.assertEqual(progress["current_level"], 51)
        self.assertEqual(progress["xp"], 321)
        self.assertEqual(progress["completed_levels"], list(range(1, 51)))

    def test_reset_clears_all_player_progress_and_reviews(self):
        attempt = main.ExerciseAttemptRequest(
            exercise_id="L001-P01-E1",
            correct=False,
            grammar_tags=["to_be"],
        )
        main.finish_level(
            1,
            database.DEFAULT_PLAYER_ID,
            main.CompletionRequest(attempts=[attempt]),
        )
        reset = main.reset_game(database.DEFAULT_PLAYER_ID)["progress"]
        self.assertEqual(reset["current_level"], 1)
        self.assertEqual(reset["xp"], 0)
        self.assertEqual(reset["completed_levels"], [])
        self.assertEqual(reset["hearts"], database.MAX_HEARTS)
        self.assertEqual(
            main.due_review_queue(100, database.DEFAULT_PLAYER_ID)["reviews"],
            [],
        )


if __name__ == "__main__":
    unittest.main()

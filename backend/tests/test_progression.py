import unittest

from app.progression import (
    FINAL_BOSS_BONUS_XP,
    MAX_PLAYER_LEVEL,
    XP_THRESHOLDS,
    get_player_level,
    get_xp_progress,
    xp_required_to_advance,
    xp_reward_for_lesson,
    xp_threshold_for_level,
)


class ProgressionTests(unittest.TestCase):

    def test_curve_contains_all_100_levels(self):
        self.assertEqual(
            len(XP_THRESHOLDS),
            MAX_PLAYER_LEVEL,
        )
        self.assertEqual(
            XP_THRESHOLDS[0],
            0,
        )
        self.assertTrue(
            all(
                later > earlier
                for earlier, later in zip(
                    XP_THRESHOLDS,
                    XP_THRESHOLDS[1:],
                )
            )
        )

    def test_late_levels_require_more_xp(self):
        self.assertLess(
            xp_required_to_advance(1),
            xp_required_to_advance(25),
        )
        self.assertLess(
            xp_required_to_advance(25),
            xp_required_to_advance(50),
        )
        self.assertLess(
            xp_required_to_advance(50),
            xp_required_to_advance(99),
        )

    def test_thresholds_map_to_player_levels(self):
        for level in (1, 2, 10, 50, 100):
            self.assertEqual(
                get_player_level(
                    xp_threshold_for_level(
                        level
                    )
                ),
                level,
            )

    def test_progress_inside_level(self):
        level = 20
        required = xp_required_to_advance(
            level
        )
        xp = (
            xp_threshold_for_level(level)
            + (required // 2)
        )
        progress = get_xp_progress(xp)

        self.assertEqual(
            progress["player_level"],
            level,
        )
        self.assertGreaterEqual(
            progress["level_progress_percent"],
            49,
        )
        self.assertLessEqual(
            progress["level_progress_percent"],
            51,
        )

    def test_lesson_rewards_follow_curve(self):
        self.assertGreaterEqual(xp_reward_for_lesson(1), 1)
        self.assertGreater(xp_reward_for_lesson(50), xp_reward_for_lesson(49))
        self.assertGreater(xp_reward_for_lesson(4951), xp_reward_for_lesson(1))
        self.assertEqual(
            xp_reward_for_lesson(5000),
            FINAL_BOSS_BONUS_XP,
        )


if __name__ == "__main__":
    unittest.main()

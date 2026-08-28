from bisect import bisect_right
from functools import lru_cache


MAX_PLAYER_LEVEL = 100
FINAL_BOSS_BONUS_XP = 5000


def xp_required_to_advance(
    level: int,
) -> int:
    if level < 1 or level >= MAX_PLAYER_LEVEL:
        return 0

    if level <= 10:
        return 40 + ((level - 1) * 10)

    if level <= 30:
        return 150 + ((level - 11) * 15)

    if level <= 60:
        return 480 + ((level - 31) * 25)

    if level <= 90:
        return 1300 + ((level - 61) * 40)

    return 2700 + ((level - 91) * 100)


@lru_cache(maxsize=MAX_PLAYER_LEVEL)
def xp_threshold_for_level(
    level: int,
) -> int:
    bounded_level = min(
        max(level, 1),
        MAX_PLAYER_LEVEL,
    )

    return sum(
        xp_required_to_advance(
            current_level
        )
        for current_level in range(
            1,
            bounded_level,
        )
    )


XP_THRESHOLDS = tuple(
    xp_threshold_for_level(level)
    for level in range(
        1,
        MAX_PLAYER_LEVEL + 1,
    )
)


def get_player_level(xp: int) -> int:
    safe_xp = max(xp, 0)

    return min(
        bisect_right(
            XP_THRESHOLDS,
            safe_xp,
        ),
        MAX_PLAYER_LEVEL,
    )


def get_xp_progress(xp: int) -> dict:
    safe_xp = max(xp, 0)
    player_level = get_player_level(
        safe_xp
    )
    current_threshold = (
        xp_threshold_for_level(
            player_level
        )
    )

    if player_level >= MAX_PLAYER_LEVEL:
        return {
            "player_level": MAX_PLAYER_LEVEL,
            "level_xp": 0,
            "level_xp_required": 0,
            "level_progress_percent": 100,
            "next_player_level": None,
            "total_xp_to_max": (
                XP_THRESHOLDS[-1]
            ),
        }

    required = xp_required_to_advance(
        player_level
    )
    level_xp = safe_xp - current_threshold
    percentage = round(
        (level_xp / required) * 100,
        1,
    )

    return {
        "player_level": player_level,
        "level_xp": level_xp,
        "level_xp_required": required,
        "level_progress_percent": min(
            percentage,
            100,
        ),
        "next_player_level": (
            player_level + 1
        ),
        "total_xp_to_max": (
            XP_THRESHOLDS[-1]
        ),
    }


def xp_reward_for_lesson(
    point_id: int,
) -> int:
    from .game_engine import POINTS_PER_LOCATION, TOTAL_POINTS

    if point_id < 1 or point_id > TOTAL_POINTS:
        raise ValueError(
            f"point_id must be between 1 and {TOTAL_POINTS}"
        )

    if point_id == TOTAL_POINTS:
        return FINAL_BOSS_BONUS_XP

    # Roughly one RPG level per location. Regular points split that location's
    # XP requirement; every 50th point is a slightly larger boss reward.
    player_band = min(
        ((point_id - 1) // POINTS_PER_LOCATION) + 1,
        MAX_PLAYER_LEVEL - 1,
    )
    required = xp_required_to_advance(player_band)
    base_reward = max(1, round(required / (POINTS_PER_LOCATION + 2)))
    return base_reward * (3 if point_id % POINTS_PER_LOCATION == 0 else 1)

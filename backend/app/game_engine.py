from typing import Optional


TOTAL_LOCATIONS = 10
LEVELS_PER_LOCATION = 10
TOTAL_LEVELS = TOTAL_LOCATIONS * LEVELS_PER_LOCATION

BOSS_PASS_PERCENTAGE = 70


def find_level(
    game_data: dict,
    level_id: int
) -> Optional[dict]:

    for location in game_data["locations"]:

        for level in location.get("levels", []):

            if level["id"] == level_id:
                return level

    return None


def find_location_for_level(
    game_data: dict,
    level_id: int
) -> Optional[dict]:

    for location in game_data["locations"]:

        for level in location.get("levels", []):

            if level["id"] == level_id:
                return location

    return None


def get_location_id(level_id: int) -> int:
    return (
        (level_id - 1)
        // LEVELS_PER_LOCATION
    ) + 1


def get_level_number_in_location(
    level_id: int
) -> int:

    return (
        (level_id - 1)
        % LEVELS_PER_LOCATION
    ) + 1


def get_next_level_id(
    level_id: int
) -> Optional[int]:

    if level_id >= TOTAL_LEVELS:
        return None

    return level_id + 1


def is_boss(level_id: int) -> bool:
    return (
        get_level_number_in_location(level_id)
        == LEVELS_PER_LOCATION
    )


def calculate_boss_result(
    correct_answers: int,
    total_answers: int
) -> dict:

    if total_answers <= 0:
        percentage = 0
    else:
        percentage = round(
            (
                correct_answers
                / total_answers
            )
            * 100
        )

    if percentage >= 95:
        rank = "S"
    elif percentage >= 85:
        rank = "A"
    elif percentage >= 75:
        rank = "B"
    elif percentage >= BOSS_PASS_PERCENTAGE:
        rank = "C"
    else:
        rank = "F"

    return {
        "correct_answers": correct_answers,
        "total_answers": total_answers,
        "percentage": percentage,
        "rank": rank,
        "passed": percentage >= BOSS_PASS_PERCENTAGE,
    }


def sanitize_level_for_client(
    level: dict
) -> dict:

    sanitized = dict(level)

    sanitized.pop("internal_notes", None)

    return sanitized
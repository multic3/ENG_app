from copy import deepcopy
from typing import Optional


TOTAL_LOCATIONS = 100
POINTS_PER_LOCATION = 50
TOTAL_POINTS = TOTAL_LOCATIONS * POINTS_PER_LOCATION

# Compatibility aliases for the existing API. A "level" in routes and the
# database is a course point; the player's RPG level is calculated from XP.
LEVELS_PER_LOCATION = POINTS_PER_LOCATION
TOTAL_LEVELS = TOTAL_POINTS

BOSS_PASS_PERCENTAGE = 70


def find_level(
    game_data: dict,
    level_id: int
) -> Optional[dict]:

    for location in game_data["locations"]:

        for level in location.get("points", location.get("levels", [])):

            if level["id"] == level_id:
                return level

    return None


def find_location_for_level(
    game_data: dict,
    level_id: int
) -> Optional[dict]:

    for location in game_data["locations"]:

        for level in location.get("points", location.get("levels", [])):

            if level["id"] == level_id:
                return location

    return None


def get_location_id(level_id: int) -> int:
    return (
        (level_id - 1)
        // POINTS_PER_LOCATION
    ) + 1


def get_level_number_in_location(
    level_id: int
) -> int:

    return (
        (level_id - 1)
        % POINTS_PER_LOCATION
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
        == POINTS_PER_LOCATION
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

    sanitized = deepcopy(level)

    sanitized.pop("internal_notes", None)

    # Keep canonical exercises in the response and expose a temporary `steps`
    # view so older installed PWAs continue working after the curriculum
    # migration. New clients should use `exercises`.
    exercises = sanitized.get("exercises")
    if exercises is not None:
        sanitized["steps"] = [
            _exercise_as_legacy_step(exercise)
            for exercise in exercises
        ]

    return sanitized


def _exercise_as_legacy_step(exercise: dict) -> dict:
    step = dict(exercise)
    step["type"] = {
        "multiple_choice": "choice",
        "fill_blank": "text",
        "speech": "speaking",
    }.get(exercise.get("type"), exercise.get("type"))
    step.setdefault("question", exercise.get("prompt", ""))
    step.setdefault("question_translation", exercise.get("translation"))
    if exercise.get("type") in {"multiple_choice", "listening"}:
        options = exercise.get("options", [])
        correct_answer = exercise.get("correct_answer")
        step["answer"] = (
            options.index(correct_answer)
            if correct_answer in options
            else -1
        )
    else:
        step.setdefault("answer", exercise.get("correct_answer", ""))
    step.setdefault("accepted_answers", exercise.get("accepted_answers", []))
    if exercise.get("type") == "fill_blank":
        step["question"] = "Complete the sentence."
        step["question_translation"] = "Вставьте пропущенное слово."
        step.setdefault("sentence", exercise.get("prompt", ""))
        step.setdefault("sentence_translation", exercise.get("translation"))
    if exercise.get("type") == "speech":
        step.setdefault(
            "phrase",
            exercise.get("phrase") or exercise.get("correct_answer", ""),
        )
        step.setdefault("phrase_translation", exercise.get("translation"))
    return step

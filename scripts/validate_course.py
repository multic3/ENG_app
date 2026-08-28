"""Validate the curriculum manifest and authored course content, then report coverage."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_TYPES = {"multiple_choice", "fill_blank", "listening", "speech"}
EXPECTED_STAGES = {
    range(1, 11): "introduction",
    range(11, 21): "guided_practice",
    range(21, 31): "context_application",
    range(31, 41): "independent_use",
    range(41, 51): "review_mission",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def expected_cefr(location_id: int) -> str:
    if location_id <= 20:
        return "A2"
    if location_id <= 60:
        return "B1"
    return "B2"


def validate_manifest(manifest: dict, errors: list[str]) -> None:
    locations = manifest.get("locations", [])
    if len(locations) != 100:
        fail(errors, f"Manifest has {len(locations)} locations; expected 100")
    if [item.get("id") for item in locations] != list(range(1, 101)):
        fail(errors, "Manifest location IDs must be consecutive 1..100")
    required = {
        "id", "cefr", "world_id", "world", "title", "topic",
        "communicative_goal", "grammar", "vocabulary", "expected_outcome",
        "theme", "points_planned", "exercises_per_point", "content_status",
    }
    for location in locations:
        location_id = location.get("id", 0)
        missing = sorted(required - location.keys())
        if missing:
            fail(errors, f"Location {location_id}: missing metadata {missing}")
        if location.get("cefr") != expected_cefr(location_id):
            fail(errors, f"Location {location_id}: incorrect CEFR band")
        if location.get("points_planned") != 50:
            fail(errors, f"Location {location_id}: points_planned must be 50")
        if location.get("exercises_per_point") != 5:
            fail(errors, f"Location {location_id}: exercises_per_point must be 5")
        expected_status = "complete" if location_id <= 2 else "planned"
        if location.get("content_status") != expected_status:
            fail(errors, f"Location {location_id}: content_status must be {expected_status}")


def validate_content(content: dict, errors: list[str]) -> dict:
    locations = content.get("locations", [])
    if [location.get("id") for location in locations] != [1, 2]:
        fail(errors, "Only fully authored locations 1 and 2 may be in course_content.json")

    ids: list[str] = []
    prompts: list[str] = []
    by_type: Counter[str] = Counter()
    by_skill: Counter[str] = Counter()
    by_grammar: Counter[str] = Counter()
    per_location: dict[int, Counter[str]] = defaultdict(Counter)
    translations = 0
    speech_count = 0
    ambiguous: list[str] = []

    for location in locations:
        location_id = location.get("id")
        points = location.get("points", [])
        if len(points) != 50:
            fail(errors, f"Location {location_id}: has {len(points)} points; expected 50")
        if [point.get("point_number") for point in points] != list(range(1, 51)):
            fail(errors, f"Location {location_id}: point numbers must be 1..50")

        previous_difficulty = 0
        for point in points:
            point_number = point["point_number"]
            expected_id = ((location_id - 1) * 50) + point_number
            if point.get("id") != expected_id:
                fail(errors, f"Location {location_id}, point {point_number}: invalid global ID")
            expected_stage = next(
                stage for numbers, stage in EXPECTED_STAGES.items()
                if point_number in numbers
            )
            if point.get("stage") != expected_stage:
                fail(errors, f"Point {expected_id}: invalid stage")
            if bool(point.get("boss")) != (point_number == 50):
                fail(errors, f"Point {expected_id}: boss flag is incorrect")

            exercises = point.get("exercises", [])
            if len(exercises) != 5:
                fail(errors, f"Point {expected_id}: has {len(exercises)} exercises; expected 5")
                continue
            types = [exercise.get("type") for exercise in exercises]
            if set(types) != EXPECTED_TYPES:
                fail(errors, f"Point {expected_id}: must contain all four exercise types")
            if any(left == right for left, right in zip(types, types[1:])):
                fail(errors, f"Point {expected_id}: adjacent exercise types repeat")

            point_difficulty = max(int(item.get("difficulty", 0)) for item in exercises)
            if point_difficulty < previous_difficulty:
                fail(errors, f"Point {expected_id}: difficulty decreases")
            previous_difficulty = point_difficulty

            for exercise in exercises:
                exercise_id = exercise.get("id", "")
                ids.append(exercise_id)
                prompts.append(str(exercise.get("prompt", "")).casefold().strip())
                by_type[exercise.get("type")] += 1
                by_skill[exercise.get("skill")] += 1
                per_location[location_id][exercise.get("type")] += 1
                by_grammar.update(exercise.get("grammar_tags", []))
                if exercise.get("translation"):
                    translations += 1

                required = {
                    "id", "cefr", "location_id", "point_id", "type", "skill",
                    "grammar_tags", "vocabulary_tags", "difficulty", "prompt",
                    "translation", "explanation",
                }
                missing = sorted(required - exercise.keys())
                if missing:
                    fail(errors, f"Exercise {exercise_id}: missing fields {missing}")
                if not exercise.get("explanation"):
                    fail(errors, f"Exercise {exercise_id}: explanation is empty")

                exercise_type = exercise.get("type")
                if exercise_type in {"multiple_choice", "listening"}:
                    options = exercise.get("options", [])
                    if len(options) < 2 or exercise.get("correct_answer") not in options:
                        fail(errors, f"Exercise {exercise_id}: answer/options mismatch")
                if exercise_type == "fill_blank":
                    if "___" not in exercise.get("prompt", ""):
                        ambiguous.append(exercise_id)
                    if not exercise.get("correct_answer"):
                        fail(errors, f"Exercise {exercise_id}: missing fill answer")
                if exercise_type == "listening":
                    if not exercise.get("audio_text") or not exercise.get("audio"):
                        fail(errors, f"Exercise {exercise_id}: missing audio settings")
                if exercise_type == "speech":
                    speech_count += 1
                    settings = exercise.get("speech_settings", {})
                    if exercise.get("mode") not in {"speech_repeat", "speech_response"}:
                        fail(errors, f"Exercise {exercise_id}: unsupported speech mode")
                    if settings.get("provider") != "browser_speech_recognition":
                        fail(errors, f"Exercise {exercise_id}: speech provider is missing")
                    if settings.get("pronunciation_assessed") is not False:
                        fail(errors, f"Exercise {exercise_id}: must not claim pronunciation grading")
                    if not exercise.get("accepted_answers"):
                        fail(errors, f"Exercise {exercise_id}: accepted speech variants missing")

    duplicate_ids = [key for key, count in Counter(ids).items() if count > 1]
    duplicate_prompts = [key for key, count in Counter(prompts).items() if count > 1]
    if duplicate_ids:
        fail(errors, f"Duplicate exercise IDs: {duplicate_ids[:5]}")
    if duplicate_prompts:
        fail(errors, f"Duplicate prompts: {duplicate_prompts[:5]}")
    if len(ids) != 500:
        fail(errors, f"Authored exercise count is {len(ids)}; expected 500")
    if ambiguous:
        fail(errors, f"Fill-blank prompts without an explicit blank: {ambiguous[:5]}")

    return {
        "locations_authored": len(locations),
        "points_authored": sum(len(item.get("points", [])) for item in locations),
        "exercises_authored": len(ids),
        "by_type": dict(sorted(by_type.items())),
        "by_skill": dict(sorted(by_skill.items())),
        "by_grammar": dict(sorted(by_grammar.items())),
        "per_location": {str(key): dict(value) for key, value in per_location.items()},
        "translation_coverage_percent": round(translations / max(len(ids), 1) * 100, 1),
        "speech_coverage_percent": round(speech_count / max(len(ids), 1) * 100, 1),
        "duplicate_ids": len(duplicate_ids),
        "duplicate_prompts": len(duplicate_prompts),
        "ambiguous_fill_blanks": len(ambiguous),
    }


def write_report(path: Path, report: dict, errors: list[str]) -> None:
    lines = [
        "# Course coverage report",
        "",
        f"Validation: **{'PASS' if not errors else 'FAIL'}**",
        "",
        f"- Curriculum manifest: 100 locations / 5,000 points / 25,000 planned exercises",
        f"- Authored now: {report['locations_authored']} locations / {report['points_authored']} points / {report['exercises_authored']} exercises",
        f"- Translation coverage: {report['translation_coverage_percent']}%",
        f"- Speech coverage: {report['speech_coverage_percent']}%",
        f"- Duplicate IDs/prompts: {report['duplicate_ids']} / {report['duplicate_prompts']}",
        f"- Ambiguous fill blanks: {report['ambiguous_fill_blanks']}",
        "",
        "## Exercise types",
        "",
        *[f"- `{key}`: {value}" for key, value in report["by_type"].items()],
        "",
        "## Grammar coverage",
        "",
        *[f"- `{key}`: {value}" for key, value in report["by_grammar"].items()],
    ]
    if errors:
        lines.extend(["", "## Errors", "", *[f"- {error}" for error in errors]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("content", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    content = json.loads(args.content.read_text(encoding="utf-8"))
    errors: list[str] = []
    validate_manifest(manifest, errors)
    report = validate_content(content, errors)
    if args.report:
        write_report(args.report, report, errors)
    if errors:
        print("Course validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Course validation passed: {report['locations_authored']} locations, "
        f"{report['points_authored']} points, {report['exercises_authored']} exercises"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the 100-location curriculum manifest from the approved specification."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LOCATION_PATTERN = re.compile(r"^(\d{1,3})\.\s+«([^»]+)»\s*$")
FIELD_PATTERN = re.compile(r"^\s*(Тема|Грамматика|Результат|Итог):\s*(.+)$")

WORLD_RANGES = (
    (1, 10, 1, "Пиксельное поселение", "village"),
    (11, 20, 2, "Городские приключения", "city"),
    (21, 30, 3, "Дорога путешественника", "journey"),
    (31, 40, 4, "Гильдия профессий", "guild"),
    (41, 50, 5, "Люди и повседневные проблемы", "neighborhood"),
    (51, 60, 6, "Информация и окружающий мир", "nature"),
    (61, 70, 7, "Карьерная цитадель", "citadel"),
    (71, 80, 8, "Пещеры знаний", "caves"),
    (81, 90, 9, "Общество и культура", "culture"),
    (91, 100, 10, "Финальная экспедиция", "final"),
)

VOCABULARY_BY_WORLD = {
    1: ["personal information", "home", "daily life", "food", "town"],
    2: ["city life", "travel", "health", "plans", "experience"],
    3: ["journeys", "events", "transport", "rules", "problems"],
    4: ["work", "skills", "projects", "meetings", "processes"],
    5: ["relationships", "money", "housing", "services", "change"],
    6: ["news", "culture", "environment", "technology", "discussion"],
    7: ["career", "leadership", "negotiation", "projects", "feedback"],
    8: ["evidence", "data", "science", "technology", "reasoning"],
    9: ["society", "climate", "economy", "education", "debate"],
    10: ["mediation", "arts", "future", "persuasion", "formal communication"],
}


def level_for(location_id: int) -> str:
    if location_id <= 20:
        return "A2"
    if location_id <= 60:
        return "B1"
    return "B2"


def world_for(location_id: int) -> tuple[int, str, str]:
    for start, end, world_id, title, theme in WORLD_RANGES:
        if start <= location_id <= end:
            return world_id, title, theme
    raise ValueError(f"No world for location {location_id}")


def parse_locations(text: str) -> list[dict]:
    section = text.split("# 7. Учебная программа на 100 локаций", 1)[1]
    section = section.split("# 8. Наполнение двух существующих локаций", 1)[0]
    lines = section.splitlines()
    parsed: list[dict] = []
    current: dict | None = None

    for raw_line in lines:
        line = raw_line.rstrip()
        location_match = LOCATION_PATTERN.match(line.strip())

        if location_match:
            if current:
                parsed.append(current)
            current = {
                "id": int(location_match.group(1)),
                "title": location_match.group(2),
            }
            continue

        if current is None:
            continue

        field_match = FIELD_PATTERN.match(line)
        if not field_match:
            continue

        field, value = field_match.groups()
        key = {
            "Тема": "topic",
            "Грамматика": "grammar_text",
            "Результат": "outcome",
            "Итог": "outcome",
        }[field]
        current[key] = value.strip()

    if current:
        parsed.append(current)

    return parsed


def build_manifest(parsed: list[dict]) -> dict:
    if [item["id"] for item in parsed] != list(range(1, 101)):
        raise ValueError("Specification must contain locations 1-100 in order")

    locations = []
    for item in parsed:
        location_id = item["id"]
        world_id, world_title, theme = world_for(location_id)
        grammar_text = item.get("grammar_text", "Интеграция изученных конструкций")
        outcome = item.get(
            "outcome",
            f"Применить материал модуля «{item['title']}» в связной ситуации.",
        )
        topic = item.get("topic", item["title"])
        grammar = [
            part.strip()
            for part in re.split(r",| и | and ", grammar_text)
            if part.strip()
        ]

        locations.append(
            {
                "id": location_id,
                "cefr": level_for(location_id),
                "world_id": world_id,
                "world": world_title,
                "title": item["title"],
                "topic": topic,
                "communicative_goal": outcome,
                "grammar": grammar,
                "grammar_summary": grammar_text,
                "vocabulary": VOCABULARY_BY_WORLD[world_id],
                "expected_outcome": outcome,
                "theme": "beach" if location_id == 2 else theme,
                "points_planned": 50,
                "exercises_per_point": 5,
                "content_status": "complete" if location_id <= 2 else "planned",
            }
        )

    return {
        "schema_version": 2,
        "course": {
            "title": "English RPG: A2 to B2",
            "locations": 100,
            "points_per_location": 50,
            "exercises_per_point": 5,
            "total_points": 5000,
            "total_exercises": 25000,
        },
        "locations": locations,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    manifest = build_manifest(
        parse_locations(args.source.read_text(encoding="utf-8"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest['locations'])} locations to {args.output}")


if __name__ == "__main__":
    main()

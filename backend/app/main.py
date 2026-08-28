import json
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import (
    advance_past_completed_levels,
    check_database,
    clamp_current_level,
    complete_level,
    get_due_reviews,
    get_player,
    get_progress,
    init_db,
    record_attempts,
    reset_progress,
    resolve_due_reviews,
    restore_hearts,
    spend_heart,
    upsert_player,
)

from .game_engine import (
    BOSS_PASS_PERCENTAGE,
    TOTAL_LEVELS,
    calculate_boss_result,
    find_level,
    find_location_for_level,
    get_location_id,
    get_next_level_id,
    is_boss,
    sanitize_level_for_client,
)
from .progression import (
    MAX_PLAYER_LEVEL,
    xp_reward_for_lesson,
)


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
CURRICULUM_FILE = BASE_DIR / "curriculum.json"
COURSE_CONTENT_FILE = BASE_DIR / "course_content.json"


app = FastAPI(
    title="English RPG",
    version="0.5.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExerciseAttemptRequest(BaseModel):
    exercise_id: str = Field(min_length=1, max_length=80)
    correct: bool
    grammar_tags: list[str] = Field(default_factory=list)


class CompletionRequest(BaseModel):
    attempts: list[ExerciseAttemptRequest] = Field(default_factory=list)


class BossResultRequest(CompletionRequest):
    correct_answers: int = Field(ge=0)
    total_answers: int = Field(gt=0)


class PlayerSessionRequest(BaseModel):
    player_id: str = Field(
        min_length=4,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    name: str = Field(min_length=1, max_length=40)


def normalize_player_id(player_id: str) -> str:
    return player_id.strip().lower()


def require_player_id(
    x_player_id: Annotated[
        str | None,
        Header(alias="X-Player-ID"),
    ] = None,
) -> str:
    if x_player_id is None:
        raise HTTPException(
            status_code=401,
            detail="Player ID is required",
        )

    player_id = normalize_player_id(x_player_id)

    if get_player(player_id) is None:
        raise HTTPException(
            status_code=401,
            detail="Unknown player ID",
        )

    return player_id


def load_game_data():
    manifest = json.loads(CURRICULUM_FILE.read_text(encoding="utf-8"))
    content = json.loads(COURSE_CONTENT_FILE.read_text(encoding="utf-8"))
    completed_content = {
        location["id"]: location
        for location in content["locations"]
    }
    locations = []
    for metadata in manifest["locations"]:
        location = {
            **metadata,
            "name": metadata["title"],
            "description": metadata["communicative_goal"],
            "points": [],
        }
        location.update(completed_content.get(metadata["id"], {}))
        locations.append(location)
    return {**manifest, "locations": locations}


GAME_DATA = load_game_data()


def get_available_level_count() -> int:
    return sum(
        len(location.get("points", []))
        for location in GAME_DATA["locations"]
    )


def get_highest_available_level_id() -> int:
    return max(
        level["id"]
        for location in GAME_DATA["locations"]
        for level in location.get("points", [])
    )


def get_available_next_level_id(
    level_id: int,
):
    next_level_id = get_next_level_id(
        level_id
    )

    if (
        next_level_id is None
        or find_level(
            GAME_DATA,
            next_level_id,
        ) is None
    ):
        return None

    return next_level_id


def validated_attempts(level: dict, attempts: list[ExerciseAttemptRequest]) -> list[dict]:
    exercises = {
        exercise["id"]: exercise
        for exercise in level.get("exercises", [])
    }
    result = []
    for attempt in attempts:
        exercise = exercises.get(attempt.exercise_id)
        if exercise is None:
            continue
        result.append(
            {
                "exercise_id": attempt.exercise_id,
                "correct": attempt.correct,
                "grammar_tags": exercise.get("grammar_tags", []),
            }
        )
    return result


@app.on_event("startup")
def startup():
    init_db()
    clamp_current_level(
        get_highest_available_level_id()
    )
    advance_past_completed_levels(
        get_highest_available_level_id()
    )


@app.get("/api/health", include_in_schema=False)
def health_check():
    return {
        "status": "ok",
        "database": (
            "ok"
            if check_database()
            else "unavailable"
        ),
        "version": app.version,
    }


@app.post("/api/players/session")
def create_player_session(
    payload: PlayerSessionRequest,
):
    player_id = normalize_player_id(
        payload.player_id
    )
    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Player name is required",
        )

    player = upsert_player(player_id, name)
    clamp_current_level(
        get_highest_available_level_id(),
        player_id,
    )
    advance_past_completed_levels(
        get_highest_available_level_id(),
        player_id,
    )

    return {
        "success": True,
        "player": player,
    }


@app.get("/api/game")
def get_game(
    player_id: str = Depends(
        require_player_id
    ),
):

    progress = get_progress(player_id)
    player_profile = get_player(player_id)

    locations = []

    for location in GAME_DATA["locations"]:

        locations.append(
            {
                "id": location["id"],
                "name": location["name"],
                "description": location["description"],
                "theme": location.get(
                    "theme",
                    "default",
                ),
                "cefr": location["cefr"],
                "world": location["world"],
                "content_status": location.get("content_status", "planned"),
            }
        )

    return {
        "player": {
            "id": player_id,
            "name": player_profile["name"],
            "xp": progress["xp"],
            "level": progress["player_level"],
            "level_xp": progress["level_xp"],
            "level_xp_required": (
                progress["level_xp_required"]
            ),
            "level_progress_percent": (
                progress[
                    "level_progress_percent"
                ]
            ),
            "max_level": MAX_PLAYER_LEVEL,
            "streak": progress["streak"],
            "hearts": progress["hearts"],
            "max_hearts": progress["max_hearts"],
        },
        "progress": progress,
        "total_levels": TOTAL_LEVELS,
        "total_locations": 100,
        "points_per_location": 50,
        "available_levels": (
            get_available_level_count()
        ),
        "locations": locations,
    }


@app.get("/api/locations")
def get_locations(
    player_id: str = Depends(require_player_id),
):

    result = []

    progress = get_progress(player_id)

    for location in GAME_DATA["locations"]:

        location_id = location["id"]

        start_level = (
            (location_id - 1) * 50
        ) + 1

        unlocked = (
            progress["current_level"]
            >= start_level
        )

        completed_count = len(
            [
                level_id
                for level_id
                in progress["completed_levels"]
                if start_level
                <= level_id
                <= location_id * 50
            ]
        )

        result.append(
            {
                "id": location_id,
                "name": location["name"],
                "description": location["description"],
                "theme": location.get(
                    "theme",
                    "default",
                ),
                "unlocked": unlocked and bool(location.get("points")),
                "completed": completed_count,
                "points": 50,
                "content_status": location.get("content_status", "planned"),
            }
        )

    return {
        "locations": result
    }


@app.get(
    "/api/locations/{location_id}"
)
def get_location(location_id: int):

    for location in GAME_DATA["locations"]:

        if location["id"] == location_id:

            return location

    raise HTTPException(
        status_code=404,
        detail="Location not found",
    )


@app.get("/api/levels/{level_id}")
def get_level(
    level_id: int,
    player_id: str = Depends(require_player_id),
):

    level = find_level(
        GAME_DATA,
        level_id,
    )

    if level is None:

        raise HTTPException(
            status_code=404,
            detail="Level not found",
        )

    location = find_location_for_level(
        GAME_DATA,
        level_id,
    )

    progress = get_progress(player_id)

    if level_id > progress["current_level"]:

        raise HTTPException(
            status_code=403,
            detail="Level is locked",
        )

    reviews_due = get_due_reviews(player_id, level_id)
    client_level = sanitize_level_for_client(
        level
    )
    for review in reviews_due:
        review_tags = set(review["grammar_tags"])
        matching = next(
            (
                exercise
                for exercise in client_level.get("exercises", [])
                if review_tags.intersection(exercise.get("grammar_tags", []))
            ),
            None,
        )
        if matching is not None:
            matching["review_for"] = review["source_exercise_id"]
            matching_step = next(
                (
                    step
                    for step in client_level.get("steps", [])
                    if step.get("id") == matching.get("id")
                ),
                None,
            )
            if matching_step is not None:
                matching_step["review_for"] = review["source_exercise_id"]
    client_level["xp"] = (
        xp_reward_for_lesson(
            level_id
        )
    )

    return {
        "level": client_level,
        "point": client_level,
        "location": {
            key: value
            for key, value in location.items()
            if key not in {"points", "levels"}
        },
        "reviews_due": reviews_due,
    }


@app.post(
    "/api/player/hearts/spend"
)
def spend_player_heart(
    player_id: str = Depends(require_player_id),
):

    success = spend_heart(player_id)

    if not success:

        raise HTTPException(
            status_code=400,
            detail="No hearts available",
        )

    return {
        "success": True,
        "progress": get_progress(player_id),
    }


@app.post(
    "/api/player/hearts/restore"
)
def restore_player_hearts(
    player_id: str = Depends(require_player_id),
):

    progress = restore_hearts(player_id)

    return {
        "success": True,
        "progress": progress,
    }


@app.post(
    "/api/levels/{level_id}/complete"
)
def finish_level(
    level_id: int,
    player_id: str = Depends(require_player_id),
    payload: CompletionRequest | None = None,
):

    level = find_level(
        GAME_DATA,
        level_id,
    )

    if level is None:

        raise HTTPException(
            status_code=404,
            detail="Level not found",
        )

    progress = get_progress(player_id)

    if level_id > progress["current_level"]:

        raise HTTPException(
            status_code=403,
            detail="Level is locked",
        )

    if is_boss(level_id):

        raise HTTPException(
            status_code=400,
            detail=(
                "Boss levels must be completed "
                "through the boss-result endpoint"
            ),
        )

    xp_reward = xp_reward_for_lesson(
        level_id
    )

    next_level_id = (
        get_available_next_level_id(
            level_id
        )
    )

    result = complete_level(
        level_id,
        xp_reward,
        next_level_id,
        player_id,
    )
    if payload is not None:
        record_attempts(
            player_id,
            level_id,
            validated_attempts(level, payload.attempts),
        )
    resolve_due_reviews(player_id, level_id)

    return {
        "success": True,
        "level_id": level_id,
        "boss": is_boss(level_id),
        "next_level": next_level_id,
        "progress": result,
    }


@app.post(
    "/api/levels/{level_id}/boss-result"
)
def finish_boss(
    level_id: int,
    payload: BossResultRequest,
    player_id: str = Depends(require_player_id),
):

    level = find_level(
        GAME_DATA,
        level_id,
    )

    if level is None:

        raise HTTPException(
            status_code=404,
            detail="Level not found",
        )

    if not is_boss(level_id):

        raise HTTPException(
            status_code=400,
            detail="This level is not a boss",
        )

    progress = get_progress(player_id)

    if level_id > progress["current_level"]:

        raise HTTPException(
            status_code=403,
            detail="Level is locked",
        )

    if (
        payload.correct_answers
        > payload.total_answers
    ):

        raise HTTPException(
            status_code=422,
            detail=(
                "correct_answers cannot be greater "
                "than total_answers"
            ),
        )

    result = calculate_boss_result(
        payload.correct_answers,
        payload.total_answers,
    )

    if not result["passed"]:
        record_attempts(
            player_id,
            level_id,
            validated_attempts(level, payload.attempts),
        )

        return {
            "success": False,
            "result": result,
            "progress": get_progress(player_id),
        }

    next_level_id = (
        get_available_next_level_id(
            level_id
        )
    )

    completed = complete_level(
        level_id,
        xp_reward_for_lesson(
            level_id
        ),
        next_level_id,
        player_id,
    )
    record_attempts(
        player_id,
        level_id,
        validated_attempts(level, payload.attempts),
    )
    resolve_due_reviews(player_id, level_id)

    return {
        "success": True,
        "result": result,
        "progress": completed,
        "next_level": next_level_id,
        "pass_threshold": BOSS_PASS_PERCENTAGE,
    }


@app.get("/api/review/due")
def due_review_queue(
    point_id: int,
    player_id: str = Depends(require_player_id),
):
    return {"reviews": get_due_reviews(player_id, point_id)}


@app.post("/api/reset")
def reset_game(
    player_id: str = Depends(require_player_id),
):

    progress = reset_progress(player_id)

    return {
        "success": True,
        "progress": progress,
    }


@app.get("/")
def serve_index():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/sw.js", include_in_schema=False)
def serve_service_worker():

    return FileResponse(
        FRONTEND_DIR / "sw.js",
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache",
        },
    )


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)

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
    ensure_minimum_xp_for_level,
    get_player,
    get_progress,
    init_db,
    reset_progress,
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
LEVELS_FILE = BASE_DIR / "levels.json"


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


class BossResultRequest(BaseModel):
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
    with open(
        LEVELS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


GAME_DATA = load_game_data()


def get_available_level_count() -> int:
    return sum(
        len(location.get("levels", []))
        for location in GAME_DATA["locations"]
    )


def get_highest_available_level_id() -> int:
    return max(
        level["id"]
        for location in GAME_DATA["locations"]
        for level in location.get("levels", [])
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


@app.on_event("startup")
def startup():
    init_db()
    clamp_current_level(
        get_highest_available_level_id()
    )
    advance_past_completed_levels(
        get_highest_available_level_id()
    )
    progress = get_progress()
    ensure_minimum_xp_for_level(
        progress["current_level"]
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
    progress = get_progress(player_id)
    ensure_minimum_xp_for_level(
        progress["current_level"],
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
            (location_id - 1) * 10
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
                <= location_id * 10
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
                "unlocked": unlocked,
                "completed": completed_count,
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

    client_level = sanitize_level_for_client(
        level
    )
    client_level["xp"] = (
        xp_reward_for_lesson(
            level_id
        )
    )

    return {
        "level": client_level,
        "location": location,
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

    return {
        "success": True,
        "result": result,
        "progress": completed,
        "next_level": next_level_id,
        "pass_threshold": BOSS_PASS_PERCENTAGE,
    }


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

import os
import json
import sqlite3
from pathlib import Path

from .progression import get_xp_progress, xp_threshold_for_level


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = (
    Path("/data")
    if os.getenv("AMVERA")
    else BASE_DIR / "data"
)
DATA_DIR = Path(
    os.getenv(
        "ENGLISH_RPG_DATA_DIR",
        str(DEFAULT_DATA_DIR),
    )
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "game.db"

MAX_HEARTS = 5
DAILY_STREAK_DEFAULT = 1
DEFAULT_PLAYER_ID = "anya"
DEFAULT_PLAYER_NAME = "Anya is a princess"
COURSE_SCHEMA_VERSION = "2"


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def check_database() -> bool:
    connection = get_connection()

    try:
        connection.execute("SELECT 1").fetchone()
        return True
    finally:
        connection.close()


def _table_columns(connection, table_name: str) -> set[str]:
    return {
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }


def _migrate_completed_levels(connection):
    columns = _table_columns(connection, "completed_levels")

    if "player_id" in columns:
        return

    connection.execute(
        "ALTER TABLE completed_levels "
        "RENAME TO completed_levels_single_player"
    )
    connection.execute(
        """
        CREATE TABLE completed_levels (
            player_id TEXT NOT NULL,
            level_id INTEGER NOT NULL,
            completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, level_id),
            FOREIGN KEY (player_id)
                REFERENCES players(player_id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        INSERT INTO completed_levels (
            player_id,
            level_id,
            completed_at
        )
        SELECT ?, level_id, completed_at
        FROM completed_levels_single_player
        """,
        (DEFAULT_PLAYER_ID,),
    )
    connection.execute("DROP TABLE completed_levels_single_player")


def _migrate_course_points(connection):
    """Expand each old 10-point location slot into five new point slots."""
    version = connection.execute(
        "SELECT value FROM app_metadata WHERE key = 'course_schema_version'"
    ).fetchone()
    if version is not None and version["value"] == COURSE_SCHEMA_VERSION:
        return

    progress_rows = connection.execute(
        "SELECT player_id, current_level FROM player_progress"
    ).fetchall()
    for row in progress_rows:
        old_id = max(1, min(int(row["current_level"]), 20))
        old_location = (old_id - 1) // 10
        old_local = (old_id - 1) % 10
        new_id = (old_location * 50) + (old_local * 5) + 1
        connection.execute(
            "UPDATE player_progress SET current_level = ? WHERE player_id = ?",
            (new_id, row["player_id"]),
        )

    completed_rows = connection.execute(
        "SELECT player_id, level_id, completed_at FROM completed_levels"
    ).fetchall()
    connection.execute("DELETE FROM completed_levels")
    for row in completed_rows:
        old_id = int(row["level_id"])
        if not 1 <= old_id <= 20:
            continue
        old_location = (old_id - 1) // 10
        old_local = (old_id - 1) % 10
        first_new_id = (old_location * 50) + (old_local * 5) + 1
        for new_id in range(first_new_id, first_new_id + 5):
            connection.execute(
                """
                INSERT OR IGNORE INTO completed_levels
                    (player_id, level_id, completed_at)
                VALUES (?, ?, ?)
                """,
                (row["player_id"], new_id, row["completed_at"]),
            )

    connection.execute(
        """
        INSERT INTO app_metadata (key, value) VALUES ('course_schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (COURSE_SCHEMA_VERSION,),
    )


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            player_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO players (player_id, name)
        VALUES (?, ?)
        """,
        (DEFAULT_PLAYER_ID, DEFAULT_PLAYER_NAME),
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS player_progress (
            id INTEGER PRIMARY KEY,
            player_id TEXT UNIQUE,
            current_level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            streak INTEGER NOT NULL DEFAULT 1,
            hearts INTEGER NOT NULL DEFAULT 5,
            FOREIGN KEY (player_id)
                REFERENCES players(player_id)
                ON DELETE CASCADE
        )
        """
    )
    progress_columns = _table_columns(connection, "player_progress")

    if "streak" not in progress_columns:
        connection.execute(
            "ALTER TABLE player_progress "
            "ADD COLUMN streak INTEGER NOT NULL DEFAULT 1"
        )
    if "hearts" not in progress_columns:
        connection.execute(
            "ALTER TABLE player_progress "
            "ADD COLUMN hearts INTEGER NOT NULL DEFAULT 5"
        )
    if "player_id" not in progress_columns:
        connection.execute(
            "ALTER TABLE player_progress ADD COLUMN player_id TEXT"
        )

    connection.execute(
        "UPDATE player_progress SET player_id = ? "
        "WHERE player_id IS NULL",
        (DEFAULT_PLAYER_ID,),
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        player_progress_player_id_idx
        ON player_progress(player_id)
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS completed_levels (
            player_id TEXT NOT NULL,
            level_id INTEGER NOT NULL,
            completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, level_id),
            FOREIGN KEY (player_id)
                REFERENCES players(player_id)
                ON DELETE CASCADE
        )
        """
    )
    _migrate_completed_levels(connection)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            point_id INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            grammar_tags TEXT NOT NULL DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            source_exercise_id TEXT NOT NULL,
            grammar_tags TEXT NOT NULL DEFAULT '[]',
            due_point_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, source_exercise_id, status),
            FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO player_progress (
            player_id,
            current_level,
            xp,
            streak,
            hearts
        )
        VALUES (?, 1, 0, ?, ?)
        """,
        (DEFAULT_PLAYER_ID, DAILY_STREAK_DEFAULT, MAX_HEARTS),
    )

    _migrate_course_points(connection)

    connection.commit()
    connection.close()


def record_attempts(
    player_id: str,
    point_id: int,
    attempts: list[dict],
):
    connection = get_connection()
    for attempt in attempts:
        tags = attempt.get("grammar_tags") or []
        serialized_tags = json.dumps(tags, ensure_ascii=False)
        correct = bool(attempt.get("correct"))
        exercise_id = str(attempt.get("exercise_id", "")).strip()
        if not exercise_id:
            continue
        connection.execute(
            """
            INSERT INTO exercise_attempts
                (player_id, exercise_id, point_id, correct, grammar_tags)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_id, exercise_id, point_id, int(correct), serialized_tags),
        )
        if not correct:
            connection.execute(
                """
                INSERT OR IGNORE INTO review_queue
                    (player_id, source_exercise_id, grammar_tags, due_point_id)
                VALUES (?, ?, ?, ?)
                """,
                (player_id, exercise_id, serialized_tags, point_id + 3),
            )
    connection.commit()
    connection.close()


def get_due_reviews(player_id: str, point_id: int) -> list[dict]:
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, source_exercise_id, grammar_tags, due_point_id
        FROM review_queue
        WHERE player_id = ? AND status = 'pending' AND due_point_id <= ?
        ORDER BY due_point_id, id
        LIMIT 5
        """,
        (player_id, point_id),
    ).fetchall()
    connection.close()
    return [
        {
            **dict(row),
            "grammar_tags": json.loads(row["grammar_tags"]),
        }
        for row in rows
    ]


def resolve_due_reviews(player_id: str, point_id: int) -> None:
    connection = get_connection()
    connection.execute(
        """
        DELETE FROM review_queue
        WHERE player_id = ? AND status = 'pending' AND due_point_id <= ?
        """,
        (player_id, point_id),
    )
    connection.commit()
    connection.close()


def upsert_player(player_id: str, name: str):
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO players (player_id, name)
        VALUES (?, ?)
        ON CONFLICT(player_id)
        DO UPDATE SET
            name = excluded.name,
            updated_at = CURRENT_TIMESTAMP
        """,
        (player_id, name),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO player_progress (
            player_id,
            current_level,
            xp,
            streak,
            hearts
        )
        VALUES (?, 1, 0, ?, ?)
        """,
        (player_id, DAILY_STREAK_DEFAULT, MAX_HEARTS),
    )
    connection.commit()
    connection.close()
    return get_player(player_id)


def get_player(player_id: str):
    connection = get_connection()
    player = connection.execute(
        "SELECT player_id, name FROM players WHERE player_id = ?",
        (player_id,),
    ).fetchone()
    connection.close()
    return dict(player) if player is not None else None


def get_progress(player_id: str = DEFAULT_PLAYER_ID):
    connection = get_connection()
    player = connection.execute(
        """
        SELECT current_level, xp, streak, hearts
        FROM player_progress
        WHERE player_id = ?
        """,
        (player_id,),
    ).fetchone()

    if player is None:
        connection.close()
        raise ValueError("Player not found")

    completed = connection.execute(
        """
        SELECT level_id
        FROM completed_levels
        WHERE player_id = ?
        ORDER BY level_id
        """,
        (player_id,),
    ).fetchall()
    connection.close()

    progress = {
        "current_level": player["current_level"],
        "xp": player["xp"],
        "streak": player["streak"],
        "hearts": player["hearts"],
        "max_hearts": MAX_HEARTS,
        "completed_levels": [row["level_id"] for row in completed],
    }
    progress.update(get_xp_progress(player["xp"]))
    return progress


def clamp_current_level(
    highest_available_level: int,
    player_id: str = DEFAULT_PLAYER_ID,
):
    connection = get_connection()
    connection.execute(
        """
        UPDATE player_progress
        SET current_level = ?
        WHERE player_id = ? AND current_level > ?
        """,
        (highest_available_level, player_id, highest_available_level),
    )
    connection.commit()
    connection.close()


def advance_past_completed_levels(
    highest_available_level: int,
    player_id: str = DEFAULT_PLAYER_ID,
):
    connection = get_connection()
    progress = connection.execute(
        """
        SELECT current_level
        FROM player_progress
        WHERE player_id = ?
        """,
        (player_id,),
    ).fetchone()

    if progress is None:
        connection.close()
        raise ValueError("Player not found")

    completed = {
        row["level_id"]
        for row in connection.execute(
            """
            SELECT level_id
            FROM completed_levels
            WHERE player_id = ?
            """,
            (player_id,),
        ).fetchall()
    }

    target_level = progress["current_level"]

    while (
        target_level in completed
        and target_level < highest_available_level
    ):
        target_level += 1

    connection.execute(
        """
        UPDATE player_progress
        SET current_level = ?
        WHERE player_id = ?
        """,
        (target_level, player_id),
    )
    connection.commit()
    connection.close()


def ensure_minimum_xp_for_level(
    level: int,
    player_id: str = DEFAULT_PLAYER_ID,
):
    minimum_xp = xp_threshold_for_level(level)
    connection = get_connection()
    connection.execute(
        """
        UPDATE player_progress
        SET xp = ?
        WHERE player_id = ? AND xp < ?
        """,
        (minimum_xp, player_id, minimum_xp),
    )
    connection.commit()
    connection.close()


def spend_heart(player_id: str = DEFAULT_PLAYER_ID):
    connection = get_connection()
    cursor = connection.execute(
        """
        UPDATE player_progress
        SET hearts = hearts - 1
        WHERE player_id = ? AND hearts > 0
        """,
        (player_id,),
    )
    connection.commit()
    connection.close()
    return cursor.rowcount == 1


def restore_hearts(player_id: str = DEFAULT_PLAYER_ID):
    connection = get_connection()
    connection.execute(
        "UPDATE player_progress SET hearts = ? WHERE player_id = ?",
        (MAX_HEARTS, player_id),
    )
    connection.commit()
    connection.close()
    return get_progress(player_id)


def complete_level(
    level_id: int,
    xp_reward: int,
    next_level_id: int | None = None,
    player_id: str = DEFAULT_PLAYER_ID,
):
    connection = get_connection()
    already_completed = connection.execute(
        """
        SELECT level_id
        FROM completed_levels
        WHERE player_id = ? AND level_id = ?
        """,
        (player_id, level_id),
    ).fetchone()

    if already_completed is None:
        connection.execute(
            "INSERT INTO completed_levels (player_id, level_id) "
            "VALUES (?, ?)",
            (player_id, level_id),
        )
        connection.execute(
            "UPDATE player_progress SET xp = xp + ? "
            "WHERE player_id = ?",
            (xp_reward, player_id),
        )

    progression_target = (
        next_level_id if next_level_id is not None else level_id
    )
    connection.execute(
        """
        UPDATE player_progress
        SET current_level = CASE
                WHEN current_level < ? THEN ?
                ELSE current_level
            END,
            hearts = ?
        WHERE player_id = ?
        """,
        (
            progression_target,
            progression_target,
            MAX_HEARTS,
            player_id,
        ),
    )
    connection.commit()
    connection.close()
    return get_progress(player_id)


def reset_progress(player_id: str = DEFAULT_PLAYER_ID):
    connection = get_connection()
    connection.execute(
        "DELETE FROM completed_levels WHERE player_id = ?",
        (player_id,),
    )
    connection.execute(
        "DELETE FROM exercise_attempts WHERE player_id = ?",
        (player_id,),
    )
    connection.execute(
        "DELETE FROM review_queue WHERE player_id = ?",
        (player_id,),
    )
    connection.execute(
        """
        UPDATE player_progress
        SET current_level = 1,
            xp = 0,
            streak = 1,
            hearts = ?
        WHERE player_id = ?
        """,
        (MAX_HEARTS, player_id),
    )
    connection.commit()
    connection.close()
    return get_progress(player_id)

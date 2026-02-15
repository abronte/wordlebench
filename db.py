import json
import sqlite3
import threading
from pathlib import Path

from models import Game

DB_PATH = Path(__file__).parent / "games.db"
_db_lock = threading.Lock()
_thread_local = threading.local()


def _configure_connection(conn: sqlite3.Connection) -> None:
    """Configure a per-connection SQLite pragmas."""
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456")


def _get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_thread_local, "conn") or _thread_local.conn is None:
        conn = sqlite3.connect(DB_PATH)
        _configure_connection(conn)
        _thread_local.conn = conn
    return _thread_local.conn


def init_db() -> None:
    """Initialize the SQLite database and create the games table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    try:
        _configure_connection(conn)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                word TEXT NOT NULL,
                guesses INTEGER DEFAULT 1,
                solved BOOLEAN DEFAULT FALSE,
                error BOOLEAN DEFAULT FALSE,
                messages TEXT DEFAULT '[]',
                cost REAL DEFAULT 0.0
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_model_word
            ON games (model, word)
        """)

        conn.commit()
    finally:
        conn.close()


def add_game(game: Game) -> None:
    """Insert a new game record into the database."""
    with _db_lock:
        conn = _get_connection()
        try:
            conn.execute(
                """
                INSERT INTO games (model, word, guesses, solved, error, messages, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game.model,
                    game.word,
                    game.guesses,
                    game.solved,
                    game.error,
                    json.dumps(game.messages),
                    game.cost,
                ),
            )
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


def check_game(model: str, word: str) -> bool:
    """Check if a game record with the given model and word already exists.

    Safe to call without the write lock — WAL mode allows concurrent reads.
    """
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT 1 FROM games WHERE model = ? AND word = ? LIMIT 1",
        (model, word),
    )
    return cursor.fetchone() is not None


def close_connection() -> None:
    """Close the thread-local database connection."""
    if hasattr(_thread_local, "conn") and _thread_local.conn is not None:
        _thread_local.conn.execute("PRAGMA optimize")
        _thread_local.conn.close()
        _thread_local.conn = None


def get_game(game_id: int) -> Game | None:
    """Retrieve a game record by its ID."""
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT id, model, word, guesses, solved, error, messages, cost FROM games WHERE id = ?",
        (game_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return Game(
        model=row[1],
        word=row[2],
        guesses=row[3],
        solved=bool(row[4]),
        error=bool(row[5]),
        messages=json.loads(row[6]),
        cost=row[7],
    )


def list_games(
    page: int = 1,
    per_page: int = 100,
    sort_by: str = "id",
    sort_order: str = "asc",
    model: str | None = None,
    word: str | None = None,
    solved: bool | None = None,
    error: bool | None = None,
) -> tuple[list[dict], int]:
    """List games with pagination, sorting, and filtering.

    Returns a tuple of (games_list, total_count).
    """
    valid_columns = {"id", "model", "word", "guesses", "solved", "error", "cost"}
    if sort_by not in valid_columns:
        sort_by = "id"
    if sort_order.lower() not in ("asc", "desc"):
        sort_order = "asc"

    conn = _get_connection()

    # Build WHERE clause for filtering
    where_clauses = []
    params = []
    if model:
        where_clauses.append("model = ?")
        params.append(model)
    if word:
        where_clauses.append("word = ?")
        params.append(word)
    if solved is not None:
        where_clauses.append("solved = ?")
        params.append(solved)
    if error is not None:
        where_clauses.append("error = ?")
        params.append(error)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # Get total count
    count_sql = f"SELECT COUNT(*) FROM games {where_sql}"
    cursor = conn.execute(count_sql, params)
    total_count = cursor.fetchone()[0]

    # Get paginated games
    offset = (page - 1) * per_page
    games_sql = f"""
        SELECT id, model, word, guesses, solved, error, cost
        FROM games
        {where_sql}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    cursor = conn.execute(games_sql, params + [per_page, offset])

    games = [
        {
            "id": row[0],
            "model": row[1],
            "word": row[2],
            "guesses": row[3],
            "solved": bool(row[4]),
            "error": bool(row[5]),
            "cost": row[6],
        }
        for row in cursor.fetchall()
    ]

    return games, total_count


def get_filter_options() -> dict:
    """Get unique values for filter dropdowns."""
    conn = _get_connection()

    cursor = conn.execute("SELECT DISTINCT model FROM games ORDER BY model")
    models = [row[0] for row in cursor.fetchall()]

    cursor = conn.execute("SELECT DISTINCT word FROM games ORDER BY word")
    words = [row[0] for row in cursor.fetchall()]

    return {"models": models, "words": words}

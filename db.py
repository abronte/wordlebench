import json
import sqlite3
import threading
from pathlib import Path

from models import Game

DB_PATH = Path(__file__).parent / "games.db"
_db_lock = threading.Lock()


def init_db():
    """Initialize the SQLite database and create the games table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
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

    conn.commit()
    conn.close()


def add_game(game: Game) -> None:
    """Insert a new game record into the database."""
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
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
        conn.close()


def check_game(model: str, word: str) -> bool:
    """Check if a game record with the given model and word already exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1 FROM games WHERE model = ? AND word = ? LIMIT 1
    """,
        (model, word),
    )

    result = cursor.fetchone()
    conn.close()

    return result is not None

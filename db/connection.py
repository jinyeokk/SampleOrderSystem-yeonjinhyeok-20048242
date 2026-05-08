import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "semi.db"


class DBConnection:
    _instance: sqlite3.Connection | None = None

    @classmethod
    def get(cls) -> sqlite3.Connection:
        if cls._instance is None:
            DB_PATH.parent.mkdir(exist_ok=True)
            cls._instance = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            cls._instance.row_factory = sqlite3.Row
            cls._instance.execute("PRAGMA foreign_keys = ON")
        return cls._instance

    @classmethod
    def close(cls) -> None:
        if cls._instance:
            cls._instance.close()
            cls._instance = None

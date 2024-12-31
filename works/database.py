"""database module."""

import sqlite3
from typing import Optional


def initialize_db(db_path: str) -> Optional[str]:
    """Initialize the SQLite database and create the necessary tables.

    Args:
        db_path (str): The path to the SQLite database.

    Returns:
        Optional[str]: None if successful, error message string if failed.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS received_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_no TEXT UNIQUE,
                channel_no TEXT,
                last_message_no INTEGER,
                message_time TEXT,
                content TEXT
            )
        """)
        conn.commit()
        return None

    except sqlite3.Error as e:
        error_msg = f"データベース初期化中にエラーが発生: {str(e)}"
        return error_msg

    finally:
        if conn:
            conn.close()

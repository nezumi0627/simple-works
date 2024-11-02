# works/database.py
import sqlite3


def initialize_db(db_path: str) -> str:
    """
    Initialize the SQLite database and create the necessary tables.

    Args:
        db_path (str): The path to the SQLite database.

    Returns:
        str: Success or error message.
    """
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
        return "Database initialized successfully."
    except sqlite3.Error as e:
        return f"Database error: {str(e)}"
    finally:
        conn.close()

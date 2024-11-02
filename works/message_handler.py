# works/message_handler.py

import json
import sqlite3
import time
from typing import Generator

import requests

from works.database import initialize_db  # Import from database.py


def receive_messages(
    headers: dict, domainId: str, userNo: str, db_path: str = "received_messages.db"
) -> Generator[dict, None, None]:
    """
    Receive messages from the server and yield them for external handling.

    Args:
        headers (dict): The headers to be used in the HTTP request.
        domainId (str): The domain ID of the user.
        userNo (str): The user number.
        db_path (str): The path to the SQLite database.

    Yields:
        dict: The received message data.
    """
    initialize_db(db_path)
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/syncUserChannelList"
    payload = {
        "serviceId": "works",
        "userKey": {"domainId": domainId, "userNo": userNo},
        "filter": "none",
        "updatePaging": True,
        "pagingCount": 100,
        "userInfoCount": 10,
        "updateTime": int(time.time() * 1000),
        "beforeMsgTime": 0,
        "isPin": True,
        "requestAgain": False,
    }
    try:
        while True:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                messages = response.json().get("result", [])
                for message in messages:
                    yield message  # Yield messages one by one
            else:
                return f"Error: Status code {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def handle_messages(messages: dict, db_path: str = "received_messages.db") -> str:
    """
    Handle received messages and store them in the database.

    Args:
        messages (dict): The received messages.
        db_path (str): The path to the SQLite database.

    Returns:
        str: Success or error message.
    """
    if not isinstance(messages, dict):
        return "Error: Received messages are not a dictionary."

    results = messages.get("result", [])
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for message in results:
        if not isinstance(message, dict):
            return f"Error: Message is not a dictionary: {message}"

        message_no = message.get("messageNo")
        cursor.execute(
            "SELECT COUNT(*) FROM received_messages WHERE message_no=?", (message_no,)
        )
        if cursor.fetchone()[0] > 0:
            continue

        try:
            cursor.execute(
                """
                INSERT INTO received_messages (message_no, channel_no, last_message_no, message_time, content)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    message_no,
                    message.get("channelNo"),
                    int(message.get("lastMessageNo", 0)),
                    message.get("messageTime", "Unknown"),
                    json.dumps(message),
                ),
            )
        except sqlite3.Error as e:
            return f"Database error: {str(e)}"

    conn.commit()
    conn.close()
    return "Messages processed successfully."

# works/message_handler.py

import json
import sqlite3
import time
from typing import Generator, Optional

import requests

from works.auth import HeaderManager  # Import from auth.py
from works.database import initialize_db  # Import from database.py


def receive_messages(
    header_manager: HeaderManager,
    domainId: str,
    userNo: str,
    db_path: str = "received_messages.db",
    polling_interval: int = 5,  # ポーリング間隔（秒）
    stop_condition: Optional[str] = None,  # 停止条件
) -> Generator[dict, None, None]:
    """
    Receive messages from the server and yield them for external handling.

    Args:
        header_manager (HeaderManager): The header manager to be used in the HTTP request.
        domainId (str): The domain ID of the user.
        userNo (str): The user number.
        db_path (str): The path to the SQLite database.
        polling_interval (int): The interval between polling requests in seconds.
        stop_condition (Optional[str]): A condition to stop polling (e.g., a specific message).

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

    while True:
        try:
            headers = header_manager.headers  # ヘッダーを取得
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                messages = response.json().get("result", [])
                for message in messages:
                    yield message  # Yield messages one by one

                    # 停止条件のチェック
                    if stop_condition and message.get("content") == stop_condition:
                        print(f"Stopping polling due to condition: {stop_condition}")
                        return
            else:
                print(f"Error: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            time.sleep(polling_interval * 2)  # エラー時は待機時間を倍増

        time.sleep(polling_interval)  # ポーリング間隔を設ける


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
            continue  # 重複メッセージはスキップ

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

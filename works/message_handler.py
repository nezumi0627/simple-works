"""Works message handler module."""

from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from works.auth import HeaderManager
from works.constants import WebSocket
from works.mqtt import connect_websocket


@dataclass
class MessageResult:
    """メッセージ処理の結果を表すデータクラス.

    Attributes:
        success: 処理が成功したかどうか
        message: 処理結果のメッセージ
        data: メッセージデータ（オプション）
    """

    success: bool
    message: str
    data: Optional[Dict] = None


async def receive_messages(
    header_manager: HeaderManager,
    domain_id: str,
    user_no: str,
    polling_interval: int = WebSocket.RETRY_INTERVAL,
    stop_condition: Optional[str] = None,
) -> AsyncGenerator[Tuple[MessageResult, Optional[Dict[str, Any]]], None]:
    """WebSocket経由でWorksのメッセージを受信する.

    Args:
        header_manager: 認証ヘッダー管理
        domain_id: ドメインID
        user_no: ユーザー番号
        polling_interval: 再接続間隔（秒）
        stop_condition: 停止条件となるメッセージ内容

    Yields:
        Tuple[MessageResult, Optional[Dict[str, Any]]]: 処理結果とメッセージデータ
    """
    try:
        async for success, message_data in connect_websocket(
            header_manager, domain_id, user_no, polling_interval
        ):
            if not success:
                yield MessageResult(False, "Connection error"), None
                continue

            if message_data:
                yield MessageResult(True, "Message received"), message_data

                if (
                    stop_condition
                    and message_data.get("content") == stop_condition
                ):
                    yield (
                        MessageResult(
                            True, f"Polling stopped: {stop_condition}"
                        ),
                        None,
                    )
                    return

    except Exception:
        raise

"""WebSocket handling for MQTT protocol."""

from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from works.auth import HeaderManager
from works.constants import WebSocket
from works.mqtt.client import MQTTClient


async def connect_websocket(
    header_manager: HeaderManager,
    domain_id: str,
    user_no: str,
    polling_interval: int = WebSocket.RETRY_INTERVAL,
) -> AsyncGenerator[Tuple[bool, Optional[Dict[str, Any]]], None]:
    """WebSocket経由でWorksのメッセージを受信する.

    Args:
        header_manager: 認証ヘッダー管理
        domain_id: ドメインID
        user_no: ユーザー番号
        polling_interval: 再接続間隔（秒）

    Yields:
        Tuple[bool, Optional[Dict[str, Any]]]: 処理結果とメッセージデータ
    """
    client = MQTTClient(header_manager)

    try:
        async for success, message_data in client.connect(domain_id, user_no):
            yield success, message_data
    except Exception:
        raise

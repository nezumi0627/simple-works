"""MQTT WebSocketクライアントの実装."""

import asyncio
import json
import ssl
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, cast

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.typing import Data, Subprotocol

from works.auth import HeaderManager
from works.constants import StatusFlag, WebSocket
from works.mqtt.packet import (
    PacketType,
    build_connect_packet,
    build_disconnect_packet,
    build_ping_packet,
    build_subscribe_packet,
    parse_packet,
    parse_publish,
)


@dataclass
class MQTTConfig:
    """MQTT接続の設定."""

    keep_alive: int = WebSocket.KEEP_ALIVE
    ping_interval: int = WebSocket.PING_INTERVAL
    ping_timeout: int = WebSocket.PING_TIMEOUT
    retry_interval: int = WebSocket.RETRY_INTERVAL
    max_retries: int = WebSocket.MAX_RETRIES


class MQTTClient:
    """MQTT WebSocketクライアント."""

    def __init__(
        self,
        header_manager: HeaderManager,
        config: Optional[MQTTConfig] = None,
    ) -> None:
        """MQTTClientを初期化します."""
        self.header_manager = header_manager
        self.config = config or MQTTConfig()

        self.running = True
        self.current_retry = 0
        self.message_id = 0
        self.ws: Optional[WebSocketClientProtocol] = None
        self._pending_messages: Dict[int, asyncio.Future] = {}
        self._received_messages: Dict[str, float] = {}
        self._message_expiry = 60.0
        self.state = StatusFlag.DISCONNECTED

    def _get_next_message_id(self) -> int:
        """次のメッセージIDを取得します."""
        self.message_id = (self.message_id + 1) % 65536
        return self.message_id

    async def connect(
        self, domain_id: str, user_no: str
    ) -> AsyncGenerator[Tuple[bool, Optional[Dict[str, Any]]], None]:
        """WebSocket接続を確立し、MQTTセッションを開始します."""
        auth_headers = self.header_manager.headers

        while self.running and self.current_retry < self.config.max_retries:
            try:
                self.state = StatusFlag.CONNECTING

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = True
                ssl_context.verify_mode = ssl.CERT_REQUIRED

                async with websockets.connect(
                    WebSocket.URL,
                    extra_headers=auth_headers,
                    subprotocols=[cast(Subprotocol, WebSocket.SUBPROTOCOL)],
                    ping_interval=None,
                    ping_timeout=None,
                    ssl=ssl_context,
                ) as websocket:
                    self.ws = websocket

                    # MQTT接続の確立
                    await self._establish_mqtt_session(domain_id, user_no)
                    self.state = StatusFlag.CONNECTED
                    self.current_retry = 0

                    # PING送信タスクを開始
                    ping_task = asyncio.create_task(
                        self._ping_loop(self.config.ping_interval)
                    )

                    try:
                        async for result in self._message_loop():
                            yield result
                    finally:
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass

            except websockets.exceptions.InvalidStatusCode:
                self.state = StatusFlag.DISCONNECTED
                self.current_retry += 1
                yield False, None

            except websockets.exceptions.ConnectionClosed:
                self.state = StatusFlag.DISCONNECTED
                self.current_retry += 1
                yield False, None

            except Exception:
                self.state = StatusFlag.DISCONNECTED
                self.current_retry += 1

                if self.current_retry >= self.config.max_retries:
                    yield False, None
                    return

                retry_delay = self.config.retry_interval * (
                    2 ** (self.current_retry - 1)
                )
                yield False, None
                await asyncio.sleep(retry_delay)

    async def _establish_mqtt_session(
        self, domain_id: str, user_no: str
    ) -> None:
        """MQTT接続を確立します."""
        if not self.ws:
            raise Exception("WebSocket connection not established")

        # CONNECT パケットの送信
        client_id = f"web-beejs_{uuid.uuid4().hex[:12]}"

        connect_packet = build_connect_packet(
            client_id=client_id,
            username="dummy",
            password=None,
            keep_alive=self.config.keep_alive,
            clean_session=True,
        )
        await self.ws.send(cast(Data, connect_packet.packet))

        # CONNACKの待機
        response = await self.ws.recv()
        if isinstance(response, bytes):
            packet = parse_packet(response)
        else:
            packet = None

        if not packet or packet.packet_type != PacketType.CONNACK:
            raise Exception("CONNACK受信に失敗しました")

        # SUBSCRIBE パケットの送信
        topics = [f"/domains/{domain_id}/users/{user_no}"]

        subscribe_packet = build_subscribe_packet(topics)
        await self.ws.send(cast(Data, subscribe_packet.packet))

        # SUBACKの待機
        response = await self.ws.recv()
        if isinstance(response, bytes):
            packet = parse_packet(response)
        else:
            packet = None

        if not packet or packet.packet_type != PacketType.SUBACK:
            raise Exception("SUBACK受信に失敗しました")

    async def _message_loop(
        self,
    ) -> AsyncGenerator[Tuple[bool, Optional[Dict[str, Any]]], None]:
        """メッセージ受信ループを実行します."""
        if not self.ws:
            raise Exception("WebSocket connection not established")

        while self.state == StatusFlag.CONNECTED:
            try:
                message = await self.ws.recv()

                if not isinstance(message, bytes):
                    continue

                packet = parse_packet(message)
                if not packet:
                    continue

                if packet.packet_type == PacketType.PINGRESP:
                    continue

                if packet.packet_type == PacketType.PUBLISH:
                    if not packet.payload:
                        continue

                    try:
                        # パケットの解析
                        topic, payload, msg_id = parse_publish(packet)

                        # ペイロードをUTF-8でデコード
                        payload_str = payload.decode(
                            "utf-8", errors="replace"
                        ).strip()
                        if not payload_str:
                            continue

                        # JSONとしてパース
                        payload_dict = json.loads(payload_str)

                        # 重複チェック
                        if self._is_duplicate_message(payload_dict):
                            continue

                        yield True, payload_dict

                    except (
                        UnicodeDecodeError,
                        json.JSONDecodeError,
                        Exception,
                    ):
                        continue

            except websockets.exceptions.ConnectionClosed:
                self.state = StatusFlag.DISCONNECTED
                break
            except Exception:
                continue

    async def _ping_loop(self, interval: int) -> None:
        """定期的にPINGを送信するループ処理."""
        while self.running and self.state == StatusFlag.CONNECTED:
            try:
                await asyncio.sleep(interval)
                if self.ws and not self.ws.closed:
                    ping_packet = build_ping_packet()
                    await self.ws.send(cast(Data, ping_packet.packet))
            except Exception:
                break

    def _is_duplicate_message(self, payload: dict) -> bool:
        """メッセージが重複しているかチェックします."""
        # メッセージキーを取得
        message_key = None
        if "notification-id" in payload:
            message_key = payload["notification-id"]
        elif "messageNo" in payload:
            message_key = f"{payload['chNo']}_{payload['messageNo']}"

        if not message_key:
            return False

        # 現在時刻を取得
        current_time = asyncio.get_event_loop().time()

        # 期限切れのメッセージを削除
        expired_keys = [
            key
            for key, timestamp in self._received_messages.items()
            if current_time - timestamp > self._message_expiry
        ]
        for key in expired_keys:
            del self._received_messages[key]

        # 重複チェック
        if message_key in self._received_messages:
            return True

        # 新しいメッセージを記録
        self._received_messages[message_key] = current_time
        return False

    async def stop(self) -> None:
        """クライアントを停止します."""
        self.running = False
        if self.ws and not self.ws.closed:
            try:
                packet = build_disconnect_packet()
                await self.ws.send(cast(Data, packet.packet))
                await self.ws.close()
                self.state = StatusFlag.DISCONNECTED
            except Exception:
                pass

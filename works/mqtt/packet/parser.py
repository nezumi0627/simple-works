"""MQTTパケット解析モジュール.

このモジュールはMQTTパケットの解析機能を提供します。
パケットのヘッダー、ペイロードの解析、および各種パケットタイプに応じた
具体的な解析機能を実装しています。
"""

import json
import struct
from typing import Any, Dict, Optional, Tuple, Union

from .base import MQTTPacket
from .types import PacketType


def analyze_packet(packet: MQTTPacket) -> Dict[str, Any]:
    """パケットの詳細な解析を行います.

    Args:
        packet: 解析対象のパケット

    Returns:
        dict: 解析結果。エラー時はエラー情報を含む辞書を返します。
    """
    result = {
        "type": packet.packet_type.name,
        "flags": {
            "dup": bool(packet.flags & 0x08),
            "qos": (packet.flags & 0x06) >> 1,
            "retain": bool(packet.flags & 0x01),
        },
        "length": packet.remaining_length,
        "raw_packet": packet.packet,
    }

    if packet.packet_type == PacketType.CONNECT:
        connect_result = parse_connect_packet(packet)
        if "error" in connect_result:
            return connect_result
        result.update(connect_result)
    elif packet.packet_type == PacketType.PUBLISH:
        try:
            topic, payload, msg_id = parse_publish(packet)
            result.update(
                {
                    "topic": topic,
                    "message_id": msg_id,
                    "payload": parse_payload(payload),
                }
            )
        except ValueError as e:
            return {"error": str(e)}

    return result


def parse_connect_packet(packet: MQTTPacket) -> Dict[str, Any]:
    """CONNECTパケットの内容を解析します.

    Args:
        packet: CONNECTパケット

    Returns:
        dict: 解析された接続情報。エラー時はエラー情報を含む辞書を返します。
    """
    if packet.payload is None:
        return {"error": "No payload in CONNECT packet"}

    try:
        # プロトコル名の長さを取得
        protocol_name_len = struct.unpack("!H", packet.payload[0:2])[0]

        # プロトコル名を取得
        protocol_name = packet.payload[2 : 2 + protocol_name_len].decode(
            "utf-8"
        )

        # プロトコルレベルを取得
        protocol_level = packet.payload[2 + protocol_name_len]

        # 接続フラグを取得
        connect_flags = packet.payload[2 + protocol_name_len + 1]

        # キープアライブを取得
        keep_alive = struct.unpack(
            "!H",
            packet.payload[
                2 + protocol_name_len + 2 : 2 + protocol_name_len + 4
            ],
        )[0]

        return {
            "protocol_name": protocol_name,
            "protocol_level": protocol_level,
            "clean_session": bool(connect_flags & 0x02),
            "will_flag": bool(connect_flags & 0x04),
            "will_qos": (connect_flags & 0x18) >> 3,
            "will_retain": bool(connect_flags & 0x20),
            "password_flag": bool(connect_flags & 0x40),
            "username_flag": bool(connect_flags & 0x80),
            "keep_alive": keep_alive,
        }
    except Exception as e:
        return {"error": f"CONNECTパケット解析エラー: {e}"}


def parse_payload(payload: bytes) -> Union[Dict[str, Any], str]:
    """ペイロードを解析します.

    Args:
        payload: 解析対象のペイロード

    Returns:
        Union[Dict[str, Any], str]: 解析結果
    """
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload.hex()


def parse_packet(data: bytes) -> Optional[MQTTPacket]:
    """バイナリデータからMQTTパケットを解析します.

    Args:
        data: 解析対象のバイナリデータ

    Returns:
        Optional[MQTTPacket]: 解析されたパケット、解析失敗時はNone
    """
    if len(data) < 2:
        return None

    try:
        packet_type = (data[0] & 0xF0) >> 4
        flags = data[0] & 0x0F

        # 可変長の残りの長さを解析
        multiplier = 1
        value = 0
        pos = 1
        while True:
            if pos >= len(data):
                return None
            byte = data[pos]
            value += (byte & 0x7F) * multiplier
            multiplier *= 128
            pos += 1
            if byte & 0x80 == 0:
                break

        remaining_length = value
        payload = (
            data[pos : pos + remaining_length]
            if remaining_length > 0
            else None
        )

        return MQTTPacket(
            packet_type=PacketType(packet_type),
            flags=flags,
            remaining_length=remaining_length,
            payload=payload,
            raw_packet=data,
        )
    except Exception:
        return None


def parse_publish(packet: MQTTPacket) -> Tuple[str, bytes, Optional[int]]:
    """PUBLISHパケットを解析します.

    Args:
        packet: PUBLISHパケット

    Returns:
        Tuple[str, bytes, Optional[int]]: トピック名、ペイロード、メッセージID

    Raises:
        ValueError: パケットの解析に失敗した場合
    """
    if not packet.payload:
        raise ValueError("No payload in PUBLISH packet")

    # トピック名の長さを取得
    topic_length = struct.unpack("!H", packet.payload[0:2])[0]

    # トピック名を取得
    topic = packet.payload[2 : 2 + topic_length].decode("utf-8")

    # QoSレベルに応じてメッセージIDを取得
    qos = (packet.flags & 0x06) >> 1
    pos = 2 + topic_length
    message_id = None

    if qos > 0:
        if len(packet.payload) < pos + 2:
            raise ValueError("Packet too short for QoS > 0")
        message_id = struct.unpack("!H", packet.payload[pos : pos + 2])[0]
        pos += 2

    # ペイロードを取得
    payload = packet.payload[pos:]

    return topic, payload, message_id

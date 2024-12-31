"""MQTT packet builder.

MQTTパケットビルダーを提供するモジュール。

主な機能:
- CONNECTパケットの生成
- PUBLISHパケットの生成
- SUBSCRIBEパケットの生成
- PINGREQパケットの生成
- DISCONNECTパケットの生成
"""

import struct
from typing import List, Optional

from .base import MQTTPacket
from .types import PacketType


def build_connect_packet(
    client_id: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    keep_alive: int = 60,
    clean_session: bool = True,
) -> MQTTPacket:
    """CONNECTパケットを生成する.

    Args:
        client_id (str): クライアントID
        username (Optional[str]): ユーザー名
        password (Optional[str]): パスワード
        keep_alive (int): キープアライブ時間(秒)。デフォルト60秒。
        clean_session (bool): セッションをクリーンに保つかどうか:デフォルトTrue

    Returns:
        MQTTPacket: 生成されたCONNECTパケット
    """
    # 可変ヘッダーの構築
    var_header = (
        b"\x00\x04"  # プロトコル名の長さ
        b"MQTT"  # プロトコル名
        b"\x04"  # プロトコルレベル
        b"\x02"  # 接続フラグ(クリーンセッション)
        + struct.pack("!H", keep_alive)  # キープアライブ
    )

    # ペイロードの構築
    payload = _encode_string(client_id)
    if username is not None:
        payload += _encode_string(username)
    if password is not None:
        payload += _encode_string(password)

    return MQTTPacket(
        packet_type=PacketType.CONNECT,
        flags=0,
        remaining_length=len(var_header) + len(payload),
        payload=var_header + payload,
    )


def build_publish_packet(
    topic: str,
    payload: bytes,
    qos: int = 0,
    retain: bool = False,
    dup: bool = False,
) -> MQTTPacket:
    """PUBLISHパケットを生成する.

    Args:
        topic (str): 発行するトピック
        payload (bytes): メッセージのペイロード
        qos (int): QoSレベル(0-2)。デフォルト0。
        retain (bool): 保持フラグ。デフォルトFalse。
        dup (bool): 再送フラグ。デフォルトFalse。

    Returns:
        MQTTPacket: 生成されたPUBLISHパケット
    """
    # フラグの設定
    flags = (dup << 3) | (qos << 1) | retain

    # 可変ヘッダーの構築
    var_header = _encode_string(topic)

    # QoS > 0の場合はメッセージIDを追加
    if qos > 0:
        var_header += struct.pack("!H", 1)  # メッセージID = 1

    return MQTTPacket(
        packet_type=PacketType.PUBLISH,
        flags=flags,
        remaining_length=len(var_header) + len(payload),
        payload=var_header + payload,
    )


def build_subscribe_packet(topics: List[str], qos: int = 0) -> MQTTPacket:
    """SUBSCRIBEパケットを生成する.

    Args:
        topics (List[str]): 購読するトピックのリスト
        qos (int): QoSレベル(0-2)。デフォルト0。

    Returns:
        MQTTPacket: 生成されたSUBSCRIBEパケット
    """
    # 可変ヘッダーの構築(メッセージID = 1)
    var_header = struct.pack("!H", 1)

    # ペイロードの構築(トピックとQoSのペア)
    payload = b"".join(
        _encode_string(topic) + bytes([qos]) for topic in topics
    )

    return MQTTPacket(
        packet_type=PacketType.SUBSCRIBE,
        flags=2,  # SUBSCRIBEは常にフラグ = 2
        remaining_length=len(var_header) + len(payload),
        payload=var_header + payload,
    )


def build_ping_packet() -> MQTTPacket:
    """PINGREQパケットを生成する.

    Returns:
        MQTTPacket: 生成されたPINGREQパケット
    """
    return MQTTPacket(
        packet_type=PacketType.PINGREQ,
        flags=0,
        remaining_length=0,
    )


def build_disconnect_packet() -> MQTTPacket:
    """DISCONNECTパケットを生成する.

    Returns:
        MQTTPacket: 生成されたDISCONNECTパケット
    """
    return MQTTPacket(
        packet_type=PacketType.DISCONNECT,
        flags=0,
        remaining_length=0,
    )


def _encode_string(s: str) -> bytes:
    """文字列をMQTT形式でエンコードする.

    Args:
        s (str): エンコードする文字列

    Returns:
        bytes: エンコードされたバイト列
    """
    encoded = s.encode("utf-8")
    return struct.pack("!H", len(encoded)) + encoded

"""MQTT protocol handling.

MQTTプロトコル処理を提供するパッケージ。

このパッケージはMQTTプロトコルのパケット処理に必要な機能を提供します。
パケットの構築、解析、および関連する型定義が含まれています。
"""

from .packet import (
    MQTTPacket,
    PacketType,
    build_connect_packet,
    build_disconnect_packet,
    build_ping_packet,
    build_publish_packet,
    build_subscribe_packet,
    parse_packet,
    parse_publish,
)
from .websocket import connect_websocket

# パブリックAPIとして公開する要素を定義
__all__ = [
    # 基本型
    "MQTTPacket",
    "PacketType",
    # パケット構築関数
    "build_connect_packet",
    "build_disconnect_packet",
    "build_ping_packet",
    "build_publish_packet",
    "build_subscribe_packet",
    # パケット解析関数
    "parse_packet",
    "parse_publish",
    # WebSocket関連
    "connect_websocket",
]

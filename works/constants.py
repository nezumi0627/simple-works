"""LINEWORKSのメッセージタイプや定数を管理するモジュール."""

import logging
from enum import Enum, IntEnum, unique
from typing import Final


@unique
class StatusFlag(IntEnum):
    """接続状態を表す列挙型."""

    DISCONNECTED = 0  # 未接続
    CONNECTING = 1  # 接続中
    CONNECTED = 2  # 接続済み


@unique
class PacketType(IntEnum):
    """MQTTパケットタイプの定数."""

    CONNECT = 1  # 接続要求
    CONNACK = 2  # 接続応答
    PUBLISH = 3  # メッセージ配信
    SUBSCRIBE = 8  # 購読要求
    SUBACK = 9  # 購読応答
    PINGREQ = 12  # Ping要求
    PINGRESP = 13  # Ping応答
    DISCONNECT = 14  # 切断要求


class MessageType(Enum):
    """メッセージタイプの定数."""

    # 基本メッセージタイプ
    TEXT = 1  # テキストメッセージ
    IMAGE = 11  # 画像
    FILE = 16  # ファイル
    STICKER = 18  # スタンプ

    # カスタムメッセージタイプ
    CUSTOM_MESSAGE = (
        30  # カスタムメッセージ（参加時に送られるボタン付きメッセージ）
    )
    USER_INFO = 26  # ユーザー情報メッセージ


class ServiceId(Enum):
    """サービスIDの定数."""

    WORKS = "works"  # LINE WORKS


class ApiEndpoint:
    """APIエンドポイントの定数."""

    BASE_URL: Final[str] = "https://talk.worksmobile.com"
    SEND_MESSAGE: Final[str] = "/p/oneapp/client/chat/sendMessage"
    RESOURCE_PATH: Final[str] = "/p/oneapp/client/chat/issueResourcePath"
    FILE_UPLOAD: Final[str] = "/p/file"
    PROFILE: Final[str] = "/v2/api/settings/profile"
    SYNC_CHANNEL: Final[str] = "/p/oneapp/client/chat/syncUserChannelList"


class WebSocket:
    """WebSocket関連の定数."""

    URL: Final[str] = "wss://jp1-web-noti.worksmobile.com/wmqtt"
    ORIGIN: Final[str] = "https://talk.worksmobile.com"
    SUBPROTOCOL: Final[str] = "mqtt"
    PING_INTERVAL: Final[int] = 30  # PING送信間隔（秒）
    PING_TIMEOUT: Final[int] = 10  # PING応答待機タイムアウト（秒）
    RETRY_INTERVAL: Final[int] = 5  # 再接続間隔（秒）
    MAX_RETRIES: Final[int] = 3  # 最大再接続試行回数
    KEEP_ALIVE: Final[int] = 50  # キープアライブ時間（秒）
    PROTOCOL_VERSION: Final[int] = 4  # MQTTプロトコルバージョン


class Logging:
    """ログ関連の定数."""

    FORMAT: Final[str] = (
        "%(asctime)s [%(levelname)s] %(name)s - "
        "%(funcName)s:%(lineno)d - %(message)s"
    )
    DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
    LEVEL: Final[int] = logging.DEBUG  # デフォルトのログレベル

"""
LINEWORKSのメッセージタイプや定数を管理するモジュール
"""


class MessageType:
    """メッセージタイプの定数"""

    # 基本メッセージタイプ
    TEXT = 1  # テキストメッセージ
    IMAGE = 11  # 画像
    FILE = 16  # ファイル
    STICKER = 18  # スタンプ

    # カスタムメッセージタイプ
    CUSTOM_LOG = 30  # カスタムログ（本来参加時に送られるボタン付きメッセージ）
    ADD_LOG = 26  # 追加ログ（ユーザー情報など）


class ServiceId:
    """サービスIDの定数"""

    WORKS = "works"  # LINE WORKS


class ApiEndpoint:
    """APIエンドポイントの定数"""

    BASE_URL = "https://talk.worksmobile.com"
    SEND_MESSAGE = "/p/oneapp/client/chat/sendMessage"
    RESOURCE_PATH = "/p/oneapp/client/chat/issueResourcePath"
    FILE_UPLOAD = "/p/file"
    PROFILE = "/v2/api/settings/profile"
    SYNC_CHANNEL = "/p/oneapp/client/chat/syncUserChannelList"


class Headers:
    """共通ヘッダーの定数"""

    CONTENT_TYPE_JSON = "application/json;charset=UTF-8"
    CONTENT_TYPE_FORM = "multipart/form-data"
    ACCEPT = "application/json, text/plain, */*"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ORIGIN = "https://talk.worksmobile.com"
    REFERER = "https://talk.worksmobile.com/"
    DEVICE_LANGUAGE = "ja_JP"
    X_TRANSLATE_LANG = "ja"

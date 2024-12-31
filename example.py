"""LINE WORKSのメッセージ送受信を行うサンプルコード."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from works.client import Works
from works.constants import Logging

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(Logging.LEVEL)

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        fmt=Logging.FORMAT,
        datefmt=Logging.DATE_FORMAT,
    )
)
logger.addHandler(handler)

# 環境変数の読み込み
load_dotenv()

# Windows環境用のイベントループポリシー設定
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 環境変数から認証情報を取得
input_id: Optional[str] = os.getenv("INPUT_ID")
password: Optional[str] = os.getenv("PASSWORD")
domain_id: Optional[str] = os.getenv("DOMAIN_ID")
user_no: Optional[str] = os.getenv("USER_NO")
temp_message_id: Optional[str] = os.getenv("TEMP_MESSAGE_ID")

# クッキーディレクトリの作成
COOKIE_DIR = Path("data")
COOKIE_DIR.mkdir(exist_ok=True)


async def send_all_messages(
    client: Works,
    channel_no: str,
    domain_id: str,
    user_no: str,
    temp_message_id: str,
) -> None:
    """全種類のメッセージを送信する.

    Args:
        client: Worksクライアントインスタンス
        channel_no: チャンネル番号
        domain_id: ドメインID
        user_no: ユーザー番号
        temp_message_id: 一時メッセージID
    """
    # 通常メッセージの送信
    await client.async_send_message(
        channel_no,
        "This is a test message from !sendall command.",
        domain_id=domain_id,
        user_no=user_no,
        temp_message_id=str(temp_message_id),
    )

    # スタンプの送信
    await client.send_sticker(
        group_id=channel_no,
        domain_id=domain_id,
        user_no=user_no,
        temp_message_id=str(temp_message_id),
        stk_type="line",
        package_id="18832978",
        sticker_id="485404830",
    )

    # カスタムログの送信
    await client.send_custom_log(
        channel_no,
        message="This is a custom log message.",
        button_message="Click Me",
        domain_id=domain_id,
        user_no=user_no,
        temp_message_id=str(temp_message_id),
    )

    # 追加ログの送信
    await client.send_add_log(
        channel_no,
        str(input_id),
        domain_id,
        user_no,
        str(temp_message_id),
        user_name="Nezumi-Works - Free Multi-Function BOT",
        desc="Nezumi-Project2024",
        lang="ja",
        photo_hash="779911d9ab14b9caaec3fd44197a1adc",
    )


async def main() -> None:
    """メインの実行関数."""
    if not all([input_id, password, domain_id, user_no, temp_message_id]):
        logger.error("必要な環境変数が設定されていません")
        return

    # Worksクライアントのインスタンス化
    client = Works(
        input_id=str(input_id),
        password=str(password),
        cookie_path=COOKIE_DIR / "cookie.json",
    )

    retry_count = 0
    max_retries = 3
    retry_delay = 5

    while retry_count < max_retries:
        try:
            # メッセージ受信処理
            async for message in client.receive_messages(
                str(domain_id),
                str(user_no),
                polling_interval=60,  # ポーリング間隔を60秒に延長
            ):
                if not isinstance(message, tuple) or len(message) != 2:
                    continue

                success, payload = message
                if not success or not payload:
                    continue

                # メッセージタイプの確認
                n_type = payload.get("nType")
                if n_type != 1:  # 通常のメッセージ以外はスキップ
                    continue

                # メッセージ内容とチャンネル番号を取得
                content = payload.get("loc-args1", "")  # メッセージ内容
                channel_no = payload.get("chNo")  # チャンネル番号

                if not channel_no:
                    continue

                # コマンド処理
                if content == "!test":
                    try:
                        await client.async_send_message(
                            str(channel_no),
                            "Hi!!",
                            domain_id=str(domain_id),
                            user_no=str(user_no),
                            temp_message_id=str(temp_message_id),
                        )
                    except Exception:
                        continue

                if content == "!sendall":
                    try:
                        await send_all_messages(
                            client,
                            str(channel_no),
                            str(domain_id),
                            str(user_no),
                            str(temp_message_id),
                        )
                    except Exception:
                        continue

        except Exception:
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数バックオフ
            else:
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}")

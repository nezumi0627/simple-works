"""Multi-account bot example.

このモジュールは、asyncioタスクを使用して複数のWorksアカウントを
同時に処理できるマルチアカウントボットシステムを実装します。
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from works.client import Works
from works.message_handler import MessageResult

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Load environment variables from examples/.env
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

# Create cookie directory if it doesn't exist
COOKIE_DIR = Path("data")
COOKIE_DIR.mkdir(exist_ok=True)


@dataclass
class AccountConfig:
    """アカウント設定を保持するデータクラス."""

    input_id: str
    password: str
    response: str


def load_account_configs() -> List[AccountConfig]:
    """環境変数からアカウント設定を読み込む.

    Returns:
        List[AccountConfig]: アカウント設定のリスト
    """
    accounts = []
    account_num = 1

    while True:
        input_id = os.getenv(f"WORKS_ID_{account_num}")
        password = os.getenv(f"WORKS_PASSWORD_{account_num}")
        response = os.getenv(f"WORKS_RESPONSE_{account_num}")

        if not all([input_id, password, response]):
            break

        accounts.append(
            AccountConfig(
                input_id=str(input_id),
                password=str(password),
                response=str(response),
            )
        )
        account_num += 1

    return accounts


class WorksBot:
    """単一アカウントのメッセージ処理を行うボットクラス."""

    def __init__(self) -> None:
        """環境設定でWorksBotを初期化する."""
        self.domain_id = os.getenv("DOMAIN_ID", "0")
        self.user_no = os.getenv("USER_NO", "0")
        self.temp_message_id = os.getenv("TEMP_MESSAGE_ID", "0")
        self.clients: Dict[str, Works] = {}

    async def handle_messages(self, account: AccountConfig) -> None:
        """特定のアカウントのメッセージを処理する.

        Args:
            account: 認証情報とレスポンスメッセージを含むアカウント設定
        """
        try:
            client = Works(
                input_id=account.input_id,
                password=account.password,
                cookie_path=COOKIE_DIR,
            )
            self.clients[account.input_id] = client

            logger.info(f"Start {account.input_id} message reception")

            async for result, message in client.receive_messages(
                self.domain_id, self.user_no
            ):
                await self._process_message(result, message, client, account)

        except Exception as e:
            logger.error(
                f"Error in message handler for {account.input_id}: {e}"
            )

    async def _process_message(
        self,
        result: MessageResult,
        message: Optional[Dict],
        client: Works,
        account: AccountConfig,
    ) -> None:
        """個々のメッセージを処理し、必要に応じて応答を送信する.

        Args:
            result: メッセージ処理結果
            message: Worksからのメッセージデータ
            client: Worksクライアントインスタンス
            account: アカウント設定
        """
        if not result.success or not message:
            logger.error(f"Message processing failed: {result.message}")
            return

        content = message.get("content", "")
        channel_no = message.get("channelNo")

        if content == "!test" and channel_no is not None:
            try:
                response = await client.async_send_message(
                    str(channel_no),
                    account.response,
                    self.domain_id,
                    self.user_no,
                    self.temp_message_id,
                )
                logger.info(f"Response from {account.input_id}: {response}")
            except Exception as e:
                logger.error(
                    f"Error sending message for {account.input_id}: {e}"
                )


class BotManager:
    """複数のボットインスタンスをasyncioタスクとして管理する."""

    def __init__(self, accounts: List[AccountConfig]):
        """アカウント設定でBotManagerを初期化する.

        Args:
            accounts: アカウント設定のリスト
        """
        self.accounts = accounts
        self.works_bot = WorksBot()
        self.tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """ボットタスクを開始し、メインループを維持する."""
        await self._start_bot_tasks()

        try:
            await self._maintain_main_loop()
        except KeyboardInterrupt:
            logger.info("\nShutting down bots...")
            for task in self.tasks:
                task.cancel()
            await asyncio.gather(*self.tasks, return_exceptions=True)

    async def _start_bot_tasks(self) -> None:
        """各アカウントのタスクを作成して開始する."""
        for account in self.accounts:
            task = asyncio.create_task(
                self.works_bot.handle_messages(account),
                name=f"Bot-{account.input_id}",
            )
            self.tasks.append(task)

    async def _maintain_main_loop(self) -> None:
        """メインループを維持し、タスクのステータスを監視する."""
        while True:
            done_tasks = [t for t in self.tasks if t.done()]
            for task in done_tasks:
                if task.exception():
                    logger.error(
                        f"Task {task.get_name()} failed: {task.exception()}"
                    )
                self.tasks.remove(task)

            if not self.tasks:
                logger.info("All bot tasks have stopped. Exiting...")
                break

            await asyncio.sleep(1)


async def main() -> None:
    """ボットシステムを初期化して実行するメイン関数."""
    accounts = load_account_configs()
    if not accounts:
        logger.error("No account configurations found in .env file")
        return

    bot_manager = BotManager(accounts)
    await bot_manager.start()


if __name__ == "__main__":
    asyncio.run(main())

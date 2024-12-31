"""Works client class."""

from pathlib import Path
from typing import AsyncGenerator, Dict, Optional, Tuple

from works.auth import AuthManager, HeaderManager
from works.message_handler import MessageResult, receive_messages
from works.message_sender import MessageSender


class Works:
    """Works client class."""

    def __init__(
        self, input_id: str, password: str, cookie_path: Optional[Path] = None
    ) -> None:
        """Initialize Works client.

        Args:
            input_id (str): User ID for login
            password (str): Password for login
            cookie_path (Optional[Path]): Path to save/load cookies.
            Defaults to None.
        """
        self.auth_manager = AuthManager(input_id, password)
        if cookie_path:
            cookie_file = f"cookie_{input_id}.json"
            cookie_path = cookie_path / cookie_file
            cookie_path.parent.mkdir(parents=True, exist_ok=True)
            self.auth_manager.cookie_path = cookie_path.resolve()
            self._cleanup_old_cookie(input_id)

        self.header_manager = HeaderManager(self.auth_manager)
        self.headers = self.header_manager.headers
        self.message_sender = MessageSender(self.header_manager)

    def _cleanup_old_cookie(self, input_id: str) -> Tuple[bool, Optional[str]]:
        """Clean up old cookie file if exists.

        Args:
            input_id (str): User ID used for cookie file name

        Returns:
            Tuple[bool, Optional[str]]: Success status and error message if any
        """
        old_cookie = Path(f"cookie_{input_id}.json")
        if old_cookie.exists():
            try:
                old_cookie.unlink()
                return True, None
            except Exception as e:
                return False, str(e)
        return True, None

    def send_message(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> Dict[str, str]:
        """Send a message to a specified group (Sync version)."""
        return self.message_sender.send_message(
            group_id, message, domain_id, user_no, temp_message_id
        )

    async def async_send_message(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> Dict[str, str]:
        """Send a message to a specified group (Async version)."""
        return await self.message_sender.async_send_message(
            group_id, message, domain_id, user_no, temp_message_id
        )

    async def send_sticker(
        self,
        group_id: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        stk_type: str = "line",
        package_id: str = "18832978",
        sticker_id: str = "485404830",
        stk_opt: str = "",
    ) -> Dict[str, str]:
        """Send a sticker to a specified group."""
        return await self.message_sender.async_send_sticker(
            group_id,
            domain_id,
            user_no,
            temp_message_id,
            stk_type,
            package_id,
            sticker_id,
            stk_opt,
        )

    async def send_custom_log(
        self,
        group_id: str,
        message: str,
        button_message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        button_url: str = "https://github.com/nezumi0627",
    ) -> Dict[str, str]:
        """Send a custom log message with a button."""
        return await self.message_sender.async_send_custom_log(
            group_id,
            message,
            button_message,
            domain_id,
            user_no,
            temp_message_id,
            button_url,
        )

    async def send_add_log(
        self,
        group_id: str,
        input_id: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        user_name: str = "ねずわーくす - 無料多機能BOT",
        desc: str = "Nezumi-Project2024",
        lang: str = "ja",
        photo_hash: str = "779911d9ab14b9caaec3fd44197a1adc",
    ) -> Dict[str, str]:
        """Send an additional log message."""
        return await self.message_sender.async_send_add_log(
            group_id,
            input_id,
            domain_id,
            user_no,
            temp_message_id,
            user_name,
            desc,
            lang,
            photo_hash,
        )

    async def receive_messages(
        self,
        domain_id: str,
        user_no: str,
        polling_interval: int = 5,
        stop_condition: Optional[str] = None,
    ) -> AsyncGenerator[Tuple[MessageResult, Optional[Dict]], None]:
        """Receive messages from Works using WebSocket."""
        async for result in receive_messages(
            self.header_manager,
            domain_id,
            user_no,
            polling_interval,
            stop_condition,
        ):
            yield result

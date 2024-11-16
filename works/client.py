# works/client.py

from pathlib import Path
from typing import Generator, Optional

from works.auth import AuthManager, HeaderManager
from works.message_handler import receive_messages
from works.message_sender import MessageSender  # Import MessageSender class


class Works:
    def __init__(
        self, input_id: str, password: str, cookie_path: Optional[Path] = None
    ) -> None:
        """
        Initialize Works client.

        Args:
            input_id (str): User ID for login
            password (str): Password for login
            cookie_path (Optional[Path]): Path to save/load cookies. Defaults to None.
        """
        # Create AuthManager with cookie path
        self.auth_manager = AuthManager(input_id, password)
        if cookie_path:
            self.auth_manager.cookie_path = cookie_path

        # Initialize HeaderManager
        self.header_manager = HeaderManager(self.auth_manager)
        self.headers = self.header_manager.headers
        self.message_sender = MessageSender(
            self.header_manager
        )  # Initialize MessageSender

    def send_message(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> str:
        """Send a message to a specified group."""
        return self.message_sender.send_message(
            group_id, message, domain_id, user_no, temp_message_id
        )

    def send_sticker(
        self,
        group_id: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        stk_type: str = "line",  # Type of the sticker
        package_id: str = "18832978",  # Package ID
        sticker_id: str = "485404830",  # Sticker ID
        stk_opt: str = "",  # Sticker options
    ) -> str:
        """Send a sticker to a specified group."""
        return self.message_sender.send_sticker(
            group_id,
            domain_id,
            user_no,
            temp_message_id,
            stk_type,
            package_id,
            sticker_id,
            stk_opt,
        )

    def send_custom_log(
        self,
        group_id: str,
        message: str,
        button_message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        button_url: str = "https://github.com/nezumi0627",
    ) -> str:
        """Send a custom log message with a button to a specified group."""
        return self.message_sender.send_custom_log(
            group_id,
            message,
            button_message,
            domain_id,
            user_no,
            temp_message_id,
            button_url,
        )

    def send_add_log(
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
    ) -> str:
        """Send an additional log message."""
        return self.message_sender.send_add_log(
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

    def receive_messages(
        self,
        domain_id: str,
        user_no: str,
        db_path: str = "received_messages.db",
        polling_interval: int = 5,
        stop_condition: Optional[str] = None,
    ) -> Generator[dict, None, None]:
        return receive_messages(
            self.header_manager,
            domain_id,
            user_no,
            db_path,
            polling_interval,
            stop_condition,
        )

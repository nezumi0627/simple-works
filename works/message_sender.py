"""LINE WORKS メッセージ送信モジュール."""

import json
from typing import Dict

import aiohttp
import requests
from aiohttp import ClientTimeout

from works.auth import HeaderManager
from works.constants import ApiEndpoint, MessageType, ServiceId


class MessageSender:
    """メッセージ送信を管理するクラス."""

    def __init__(self, header_manager: HeaderManager) -> None:
        """MessageSenderを初期化する.

        Args:
            header_manager (HeaderManager):認証済みヘッダー情報を管理する
        """
        self.header_manager = header_manager
        self.headers = self.header_manager.headers

    def send_message(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> Dict[str, str]:
        """指定したグループにメッセージを送信する（同期版）."""
        payload = self._create_payload(
            group_id, message, domain_id, user_no, temp_message_id
        )
        return self._post_request(ApiEndpoint.SEND_MESSAGE, payload)

    async def async_send_message(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> Dict[str, str]:
        """指定したグループにメッセージを送信する（非同期版）."""
        payload = self._create_payload(
            group_id, message, domain_id, user_no, temp_message_id
        )
        return await self._async_post_request(
            ApiEndpoint.SEND_MESSAGE, payload
        )

    async def async_send_sticker(
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
        """スタンプを送信する（非同期版）."""
        extras = {
            "stkType": stk_type,
            "pkgVer": "",
            "pkgId": package_id,
            "stkId": sticker_id,
            "stkOpt": stk_opt,
        }
        payload = {
            "serviceId": ServiceId.WORKS.value,
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": json.dumps(extras),
            "type": MessageType.STICKER.value,
        }
        return await self._async_post_request(
            ApiEndpoint.SEND_MESSAGE, payload
        )

    async def async_send_custom_log(
        self,
        group_id: str,
        message: str,
        button_message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        button_url: str = "https://github.com/nezumi0627",
    ) -> Dict[str, str]:
        """カスタムログメッセージを送信する（非同期版）."""
        extras = {
            "linkUrl": button_url,
            "linkText": button_message,
        }
        payload = {
            "serviceId": ServiceId.WORKS.value,
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": json.dumps(extras),
            "content": message,
            "type": MessageType.CUSTOM_MESSAGE.value,
        }
        return await self._async_post_request(
            ApiEndpoint.SEND_MESSAGE, payload
        )

    async def async_send_add_log(
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
        """追加ログメッセージを送信する（非同期版）."""
        extras = {
            "inputId": input_id,
            "userName": user_name,
            "desc": desc,
            "lang": lang,
            "photoHash": photo_hash,
        }
        payload = {
            "serviceId": ServiceId.WORKS.value,
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": json.dumps(extras),
            "type": MessageType.USER_INFO.value,
        }
        return await self._async_post_request(
            ApiEndpoint.SEND_MESSAGE, payload
        )

    def _create_payload(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> Dict:
        """メッセージ送信用のペイロードを作成する.

        Args:
            group_id (str): 送信先グループID
            message (str): 送信するメッセージ
            domain_id (str): ドメインID
            user_no (str): ユーザー番号
            temp_message_id (str): 一時メッセージID

        Returns:
            Dict: 送信用ペイロード
        """
        return {
            "serviceId": ServiceId.WORKS.value,
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": "",
            "content": message,
            "type": MessageType.TEXT.value,
        }

    def _post_request(self, endpoint: str, payload: Dict) -> Dict[str, str]:
        """POSTリクエストを送信する（同期版）.

        Args:
            endpoint (str): APIエンドポイント
            payload (Dict): 送信するデータ

        Returns:
            Dict[str, str]: レスポンス結果
        """
        try:
            response = requests.post(
                f"{ApiEndpoint.BASE_URL}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            return {
                "success": str(response.status_code == 200),
                "status_code": str(response.status_code),
                "message": (
                    "Success"
                    if response.status_code == 200
                    else f"Failed with status code: {response.status_code}"
                ),
            }
        except Exception as e:
            return {
                "success": "false",
                "status_code": "500",
                "message": f"Request failed: {str(e)}",
            }

    async def _async_post_request(
        self, endpoint: str, payload: Dict
    ) -> Dict[str, str]:
        """POSTリクエストを送信する（非同期版）.

        Args:
            endpoint (str): APIエンドポイント
            payload (Dict): 送信するデータ

        Returns:
            Dict[str, str]: レスポンス結果
        """
        timeout = ClientTimeout(total=30)
        try:
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.post(
                    f"{ApiEndpoint.BASE_URL}{endpoint}",
                    headers=self.headers,
                    json=payload,
                ) as response,
            ):
                status = response.status
                return {
                    "success": str(status == 200),
                    "status_code": str(status),
                    "message": (
                        "Success"
                        if status == 200
                        else f"Failed with status code: {status}"
                    ),
                }
        except Exception as e:
            return {
                "success": "false",
                "status_code": "500",
                "message": f"Request failed: {str(e)}",
            }

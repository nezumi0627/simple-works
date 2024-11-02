# works/message_sender.py

import json

import requests

from works.auth import HeaderManager  # Import from auth.py


class MessageSender:
    def __init__(self, header_manager: HeaderManager):
        self.header_manager = header_manager
        self.headers = self.header_manager.headers

    def send_message(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> str:
        """Send a message to a specified group."""
        url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
        payload = self._create_payload(
            group_id, message, domain_id, user_no, temp_message_id
        )
        return self._post_request(url, payload)

    def _create_payload(
        self,
        group_id: str,
        message: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
    ) -> dict:
        """Create the payload for sending a message."""
        return {
            "serviceId": "works",
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": "",
            "content": message,
            "type": 1,
        }

    def _post_request(self, url: str, payload: dict) -> str:
        """Send a POST request and return the response."""
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return "Message sent successfully!"
        else:
            return f"Error: Message sending failed. Status code: {response.status_code}"

    def send_sticker(
        self,
        group_id: str,
        domain_id: str,
        user_no: str,
        temp_message_id: str,
        stk_type: str = "line",  # Type of the sticker
        package_id: str = "18832978",  # Package ID
        stk_id: str = "485404830",  # Sticker ID
        stk_opt: str = "",  # Sticker options
    ) -> str:
        """Send a sticker to a specified group."""
        url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
        extras = {
            "stkType": stk_type,
            "pkgVer": "",
            "pkgId": package_id,
            "stkId": stk_id,
            "stkOpt": stk_opt,
        }
        payload = {
            "serviceId": "works",
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": json.dumps(extras),
            "type": 18,  # Type for sending a sticker
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return "Sticker sent successfully!"
        return f"Error: Sticker sending failed. Status code: {response.status_code}"

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
        url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
        extras = {
            "text": button_message,
            "url": button_url,
        }
        payload = {
            "serviceId": "works",
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": json.dumps(extras),
            "content": message,
            "type": 30,  # Type for custom log with button
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return "Custom log message sent successfully!"
        return f"Error: Custom log message sending failed. Status code: {response.status_code}"

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
        """Send an addition log to a specified group."""
        url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
        payload = {
            "serviceId": "works",
            "channelNo": group_id,
            "tempMessageId": temp_message_id,
            "caller": {"domainId": domain_id, "userNo": user_no},
            "extras": {
                "account": input_id,
                "userName": user_name,
                "desc": desc,
                "lang": lang,
                "photoHash": photo_hash,
            },
            "type": 26,
        }
        payload["extras"] = json.dumps(payload["extras"])
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return "User addition log sent successfully!"
        else:
            return f"Error: User addition log sending failed. Status code: {response.status_code}"

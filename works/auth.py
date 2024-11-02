# works/auth.py

import json
from typing import Optional

import requests


class AuthManager:
    def __init__(self, input_id: str, password: str):
        self.input_id = input_id
        self.password = password

    def login(self) -> Optional[str]:
        """
        Log in to the service and return cookies as a JSON string.

        Returns:
            Optional[str]: JSON string of cookies if login is successful, None otherwise.
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"https://auth.worksmobile.com/login/login?accessUrl=https://talk.worksmobile.com/&loginParam={self.input_id}",
            "Origin": "https://talk.worksmobile.com",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        try:
            login_page_response = requests.get(
                "https://auth.worksmobile.com/login/login?accessUrl=https://talk.worksmobile.com/",
                headers=headers,
            )
            login_page_response.raise_for_status()
            payload = {
                "accessUrl": "https://talk.worksmobile.com/",
                "inputId": self.input_id,
                "password": self.password,
                "keepLoginYn": "N",
            }
            response = requests.post(
                "https://auth.worksmobile.com/login/loginProcessV2",
                headers=headers,
                data=payload,
                allow_redirects=False,
            )
            response.raise_for_status()
            cookies_dict = {cookie.name: cookie.value for cookie in response.cookies}
            return json.dumps(cookies_dict, indent=4, ensure_ascii=False)
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"


class HeaderManager:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.headers = self.create_headers()

    def create_headers(self) -> dict:
        cookies_json = self.auth_manager.login()
        if cookies_json and not cookies_json.startswith("Error:"):
            cookies_dict = json.loads(cookies_json)
            return {
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Cookie": self.cookies_to_header(cookies_dict),
            }
        else:
            raise Exception(f"Login failed: {cookies_json}")

    def cookies_to_header(self, cookies_dict: dict) -> str:
        """
        Convert a dictionary of cookies to a header string.

        Args:
            cookies_dict (dict): A dictionary of cookies.

        Returns:
            str: A string representation of cookies for the header.
        """
        return "; ".join(f"{name}={value}" for name, value in cookies_dict.items())

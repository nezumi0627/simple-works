# works/auth.py

import json
from typing import Optional

import requests


def login(input_id: str, password: str) -> Optional[str]:
    """
    Log in to the service and return cookies as a JSON string.

    Args:
        input_id (str): The input ID for login.
        password (str): The password for login.

    Returns:
        Optional[str]: JSON string of cookies if login is successful, None otherwise.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"https://auth.worksmobile.com/login/login?accessUrl=https://talk.worksmobile.com/&loginParam={input_id}",
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
            "inputId": input_id,
            "password": password,
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


def cookies_to_header(cookies_dict: dict) -> str:
    """
    Convert a dictionary of cookies to a header string.

    Args:
        cookies_dict (dict): A dictionary of cookies.

    Returns:
        str: A string representation of cookies for the header.
    """
    return "; ".join(f"{name}={value}" for name, value in cookies_dict.items())

"""Authentication module for Works.

This module provides authentication functionality for the Works platform,
including cookie management and header generation for API requests.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException


class AuthManager:
    """Authentication manager for Works.

    Handles user authentication, cookie management, and session maintenance
    for the Works platform.

    Attributes:
        input_id (str): User ID for authentication
        password (str): User password
        cookie_path (Path): Path to cookie storage file
        session (requests.Session): HTTP session for requests
        _last_login_time (float): Timestamp of last login attempt
        _login_cooldown (float): Minimum time between login attempts
    """

    def __init__(self, input_id: str, password: str) -> None:
        """Initialize the AuthManager.

        Args:
            input_id (str): User ID for authentication
            password (str): User password
        """
        self.input_id = input_id
        self.password = password
        self.cookie_path = Path("cookie.json")
        self.session = requests.Session()
        self._last_login_time: float = 0
        self._login_cooldown: float = 300  # 5分のクールダウン

    def save_cookies(self, cookies_json: str) -> None:
        """Save cookies to a JSON file.

        Args:
            cookies_json (str): JSON string of cookies to save

        Raises:
            OSError: If saving cookies fails
        """
        try:
            self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_path, "w", encoding="utf-8") as f:
                f.write(cookies_json)
        except OSError as e:
            raise OSError(
                f"Failed to save cookies for {self.input_id}: {e}"
            ) from e

    def load_cookies(self) -> Optional[str]:
        """Load cookies from the JSON file if it exists.

        Returns:
            Optional[str]: JSON string of cookies if file exists and valid,
              None otherwise
        """
        try:
            if self.cookie_path.exists():
                with open(self.cookie_path, encoding="utf-8") as f:
                    cookies_data = f.read()
                    json.loads(cookies_data)  # Validate JSON format
                    return cookies_data
            return None
        except (OSError, json.JSONDecodeError):
            self._delete_cookie_file()
            return None

    def _delete_cookie_file(self) -> None:
        """Delete the cookie file if it exists."""
        if self.cookie_path.exists():
            self.cookie_path.unlink()

    def _can_login(self) -> bool:
        """Check if enough time has passed since the last login attempt.

        Returns:
            bool: True if login is allowed, False otherwise
        """
        current_time = time.time()
        if current_time - self._last_login_time >= self._login_cooldown:
            self._last_login_time = current_time
            return True
        return False

    def login(self) -> Optional[str]:
        """Log in to the service and return cookies as a JSON string.

        Returns:
            Optional[str]: JSON string containing authentication cookies

        Raises:
            Exception: If login fails or rate limit is exceeded
        """
        # Try to load existing cookies first
        if existing_cookies := self.load_cookies():
            try:
                if self._verify_cookies(existing_cookies):
                    return existing_cookies
            except Exception:
                self._delete_cookie_file()

        if not self._can_login():
            raise Exception(
                f"Login attempt too frequent for {self.input_id}. "
                f"Please wait {self._login_cooldown} seconds."
            )

        return self._perform_login()

    def _perform_login(self) -> str:
        """Perform the actual login request.

        Returns:
            str: JSON string containing authentication cookies

        Raises:
            Exception: If login fails
        """
        headers = self._get_default_headers()

        try:
            response = self._make_login_request(headers)
            all_cookies = self._extract_cookies(response)

            response_data = self._process_login_response(response, all_cookies)

            redirect_url = response_data.get("redirectUrl")
            if redirect_url and "/phone/integrate" in redirect_url:
                all_cookies = self._handle_phone_integration(
                    headers, all_cookies
                )

            return self._finalize_login(all_cookies)

        except RequestException as e:
            raise Exception(f"Network error - {str(e)}") from e
        except Exception as e:
            raise Exception(
                f"Login failed for {self.input_id}: {str(e)}"
            ) from e
        finally:
            self.session.close()

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests.

        Returns:
            Dict[str, str]: Default headers
        """
        return {
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

    def _make_login_request(
        self, headers: Dict[str, str]
    ) -> requests.Response:
        """Make the login request.

        Args:
            headers (Dict[str, str]): Request headers

        Returns:
            requests.Response: Response from login request
        """
        payload = {
            "accessUrl": "https://talk.worksmobile.com/",
            "inputId": self.input_id,
            "password": self.password,
            "keepLoginYn": "N",
        }

        return self.session.post(
            "https://auth.worksmobile.com/login/loginProcessV2",
            headers=headers,
            data=payload,
            allow_redirects=False,
            timeout=30,
        )

    def _extract_cookies(self, response: requests.Response) -> Dict[str, str]:
        """Extract cookies from response.

        Args:
            response (requests.Response): Response containing cookies

        Returns:
            Dict[str, str]: Dictionary of cookies
        """
        cookies: Dict[str, str] = {}
        for cookie in response.cookies:
            if cookie.value is not None:
                cookies[cookie.name] = str(cookie.value)
        return cookies

    def _process_login_response(
        self, response: requests.Response, all_cookies: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process the login response and validate cookies.

        Args:
            response (requests.Response): Login response
            all_cookies (Dict[str, str]): Current cookies

        Returns:
            Dict[str, Any]: Processed response data

        Raises:
            Exception: If login validation fails
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise Exception("Invalid response format from server") from e

        if not all_cookies.get("WORKS_USER_ID"):
            raise Exception("Login failed: Invalid credentials")

        return response_data

    def _log_login_response(
        self, response_data: Dict[str, Any], all_cookies: Dict[str, str]
    ) -> Tuple[str, str, str, str, List[str]]:
        """Get login response details.

        Args:
            response_data (Dict[str, Any]): Response data
            all_cookies (Dict[str, str]): Current cookies

        Returns:
            Tuple[str, str, str, str, List[str]]:
            Tuple containing login response details
        """
        return (
            f"Login response for {self.input_id}",
            f"Result code: {response_data.get('resultCode')}",
            f"Error message: {response_data.get('errorMessage', '')}",
            f"Redirect URL: {response_data.get('redirectUrl', '')}",
            list(all_cookies.keys()),
        )

    def _handle_phone_integration(
        self, headers: Dict[str, str], all_cookies: Dict[str, str]
    ) -> Dict[str, str]:
        """Handle phone integration redirect if needed.

        Args:
            headers (Dict[str, str]): Request headers
            all_cookies (Dict[str, str]): Current cookies

        Returns:
            Dict[str, str]: Updated cookies
        """
        try:
            headers["Cookie"] = self.cookies_to_header(all_cookies)
            skip_response = self.session.get(
                "https://talk.worksmobile.com/",
                headers=headers,
                allow_redirects=True,
                timeout=30,
            )
            return {
                **all_cookies,
                **{
                    cookie.name: str(cookie.value)
                    if cookie.value is not None
                    else ""
                    for cookie in skip_response.cookies
                },
            }
        except Exception:
            return all_cookies

    def _finalize_login(self, all_cookies: Dict[str, str]) -> str:
        """Finalize login by validating and saving cookies.

        Args:
            all_cookies (Dict[str, str]): Cookies to save

        Returns:
            str: JSON string of cookies

        Raises:
            Exception: If essential cookies are missing
        """
        if all_cookies.get("WORKS_USER_ID") and all_cookies.get("WORKS_SES"):
            cookies_json = json.dumps(
                all_cookies, indent=4, ensure_ascii=False
            )
            self.save_cookies(cookies_json)
            return cookies_json
        raise Exception("Login failed: Missing essential cookies")

    def _verify_cookies(self, cookies_json: str) -> bool:
        """Verify if the stored cookies are still valid.

        Args:
            cookies_json (str): JSON string of cookies to verify

        Returns:
            bool: True if cookies are valid

        Raises:
            Exception: If verification fails
        """
        try:
            cookies_dict = json.loads(cookies_json)
            headers = {
                "Cookie": self.cookies_to_header(cookies_dict),
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            }

            response = requests.get(
                "https://talk.worksmobile.com/p/contact/info",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                return True
            raise Exception("Invalid or expired cookies")

        except Exception as e:
            raise Exception(f"Cookie verification failed: {str(e)}") from e

    @staticmethod
    def cookies_to_header(cookies_dict: Dict[str, str]) -> str:
        """Convert cookies dictionary to header string.

        Args:
            cookies_dict (Dict[str, str]): Dictionary of cookies

        Returns:
            str: Cookie header string
        """
        return "; ".join(
            f"{name}={value}" for name, value in cookies_dict.items()
        )


class HeaderManager:
    """Manages HTTP headers for API requests.

    Handles creation and management of headers including authentication cookies
    for API requests to the Works platform.

    Attributes:
        auth_manager (AuthManager): Authentication manager instance
        headers (Dict[str, str]): Request headers
    """

    def __init__(self, auth_manager: AuthManager) -> None:
        """Initialize the HeaderManager.

        Args:
            auth_manager (AuthManager): Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.headers = self.create_headers()

    def create_headers(self) -> Dict[str, str]:
        """Create headers with authentication cookies.

        Returns:
            Dict[str, str]: Headers dictionary with cookies and other required
            headers

        Raises:
            Exception: If login fails
        """
        cookies_json = self.auth_manager.login()
        if not cookies_json:
            raise Exception(
                f"Login failed for user {self.auth_manager.input_id}"
            )

        cookies_dict = json.loads(cookies_json)
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Cookie": self.cookies_to_header(cookies_dict),
        }

    @staticmethod
    def cookies_to_header(cookies_dict: Dict[str, str]) -> str:
        """Convert a dictionary of cookies to a header string.

        Args:
            cookies_dict (Dict[str, str]): A dictionary of cookies

        Returns:
            str: A string representation of cookies for the header
        """
        return "; ".join(
            f"{name}={value}" for name, value in cookies_dict.items()
        )

# works/auth.py

import json
import time
from pathlib import Path
from typing import Dict, Optional

import requests
from requests.exceptions import RequestException


class AuthManager:
    def __init__(self, input_id: str, password: str):
        self.input_id = input_id
        self.password = password
        self.cookie_path = Path("cookie.json")
        self.session = requests.Session()
        self._last_login_time: float = 0
        self._login_cooldown: float = 300  # 5分のクールダウン

    def save_cookies(self, cookies_json: str) -> None:
        """
        Save cookies to a JSON file.

        Args:
            cookies_json (str): JSON string of cookies to save
        """
        try:
            self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_path, "w", encoding="utf-8") as f:
                f.write(cookies_json)
        except IOError as e:
            raise IOError(f"Failed to save cookies for {self.input_id}: {e}")

    def load_cookies(self) -> Optional[str]:
        """
        Load cookies from the JSON file if it exists.

        Returns:
            Optional[str]: JSON string of cookies if file exists and valid, None otherwise
        """
        try:
            if self.cookie_path.exists():
                with open(self.cookie_path, "r", encoding="utf-8") as f:
                    cookies_data = f.read()
                    # Validate JSON format
                    json.loads(cookies_data)  # Will raise JSONDecodeError if invalid
                    return cookies_data
            return None
        except (IOError, json.JSONDecodeError) as e:
            print(f"Failed to load cookies for {self.input_id}: {e}")
            # Delete invalid cookie file
            if self.cookie_path.exists():
                self.cookie_path.unlink()
            return None

    def _can_login(self) -> bool:
        """Check if enough time has passed since the last login attempt."""
        current_time = time.time()
        if current_time - self._last_login_time >= self._login_cooldown:
            self._last_login_time = current_time
            return True
        return False

    def login(self) -> Optional[str]:
        """
        Log in to the service and return cookies as a JSON string.
        """
        # Try to load existing cookies first
        existing_cookies = self.load_cookies()
        if existing_cookies:
            try:
                self._verify_cookies(existing_cookies)
                return existing_cookies
            except Exception:
                if self.cookie_path.exists():
                    self.cookie_path.unlink()

        # Check login cooldown
        if not self._can_login():
            raise Exception(
                f"Login attempt too frequent for {self.input_id}. "
                f"Please wait {self._login_cooldown} seconds."
            )

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
            # Direct login attempt
            payload = {
                "accessUrl": "https://talk.worksmobile.com/",
                "inputId": self.input_id,
                "password": self.password,
                "keepLoginYn": "N",
            }

            response = self.session.post(
                "https://auth.worksmobile.com/login/loginProcessV2",
                headers=headers,
                data=payload,
                allow_redirects=False,
                timeout=30,
            )

            # Get initial cookies from response
            all_cookies = {cookie.name: cookie.value for cookie in response.cookies}

            try:
                response_data = response.json()
                result_code = response_data.get("resultCode")
                error_message = response_data.get("errorMessage", "")
                redirect_url = response_data.get("redirectUrl", "")

                # Debug information
                print(f"Login response for {self.input_id}:")
                print(f"Result code: {result_code}")
                print(f"Error message: {error_message}")
                print(f"Redirect URL: {redirect_url}")
                print(f"Cookies received: {list(all_cookies.keys())}")

                # Check login result
                if not all_cookies.get("WORKS_USER_ID"):
                    raise Exception("Login failed: Invalid credentials")

                # Handle phone integration redirect if needed
                if redirect_url and "/phone/integrate" in redirect_url:
                    print(f"Phone integration required for {self.input_id}")
                    try:
                        headers["Cookie"] = self.cookies_to_header(all_cookies)
                        skip_response = self.session.get(
                            "https://talk.worksmobile.com/",
                            headers=headers,
                            allow_redirects=True,
                            timeout=30,
                        )
                        for cookie in skip_response.cookies:
                            all_cookies[cookie.name] = cookie.value
                    except Exception as e:
                        print(f"Warning: Phone integration handling failed: {e}")

                # Save and return cookies if we have the essential ones
                if all_cookies.get("WORKS_USER_ID") and all_cookies.get("WORKS_SES"):
                    cookies_json = json.dumps(all_cookies, indent=4, ensure_ascii=False)
                    self.save_cookies(cookies_json)
                    print(f"Successfully logged in as {self.input_id}")
                    return cookies_json
                else:
                    raise Exception("Login failed: Missing essential cookies")

            except json.JSONDecodeError:
                raise Exception("Invalid response format from server")

        except RequestException as e:
            error_msg = f"Network error - {str(e)}"
            raise Exception(error_msg)
        except Exception as e:
            error_msg = str(e)
            raise Exception(f"Login failed for {self.input_id}: {error_msg}")
        finally:
            self.session.close()

    def _verify_cookies(self, cookies_json: str) -> bool:
        """
        Verify if the stored cookies are still valid.

        Args:
            cookies_json (str): JSON string of cookies to verify

        Returns:
            bool: True if cookies are valid, False otherwise

        Raises:
            Exception: If verification fails
        """
        try:
            cookies_dict = json.loads(cookies_json)
            headers = {
                "Cookie": "; ".join(
                    f"{name}={value}" for name, value in cookies_dict.items()
                ),
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            }

            # Try to access a protected endpoint
            response = requests.get(
                "https://talk.worksmobile.com/p/contact/info",
                headers=headers,
                timeout=30,
            )

            # Check if the response indicates valid authentication
            if response.status_code == 200:
                return True
            raise Exception("Invalid or expired cookies")

        except Exception as e:
            raise Exception(f"Cookie verification failed: {str(e)}")

    @staticmethod
    def cookies_to_header(cookies_dict: Dict[str, str]) -> str:
        """Convert cookies dictionary to header string."""
        return "; ".join(f"{name}={value}" for name, value in cookies_dict.items())


class HeaderManager:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.headers = self.create_headers()

    def create_headers(self) -> Dict[str, str]:
        """
        Create headers with authentication cookies.

        Returns:
            Dict[str, str]: Headers dictionary with cookies and other required headers.
        """
        cookies_json = self.auth_manager.login()
        if not cookies_json:
            raise Exception(f"Login failed for user {self.auth_manager.input_id}")

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

    @staticmethod
    def cookies_to_header(cookies_dict: Dict[str, str]) -> str:
        """
        Convert a dictionary of cookies to a header string.

        Args:
            cookies_dict (Dict[str, str]): A dictionary of cookies.

        Returns:
            str: A string representation of cookies for the header.
        """
        return "; ".join(f"{name}={value}" for name, value in cookies_dict.items())

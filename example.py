# example.py

import asyncio
import json
import sys

# Import necessary functions from the works module
from works.auth import cookies_to_header, login
from works.message_handler import receive_messages
from works.message_sender import send_message

# Set the appropriate event loop policy for Windows platform
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Credentials
input_id = ""  # Works ID: e.g., example@test
password = ""  # Works password: e.g., password
domainId = 400512308  # Works domain ID
userNo = 110002509504044  # Works bot account ID
tempMessageId = 733428260  # Temporary message ID (set as needed)

# Log in and retrieve cookies
cookies_json = login(input_id, password)
if cookies_json:
    cookies_dict = json.loads(cookies_json)
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Cookie": cookies_to_header(cookies_dict),
    }

    # Message receiving process
    for message in receive_messages(headers, domainId, userNo):
        # Respond if the message content is "!test"
        content = message.get("content", "")
        channel_no = message.get("channelNo")

        if content == "!test":
            try:
                response = send_message(
                    channel_no,
                    "Hi!!",  # Response message
                    headers,
                    domain_id=domainId,
                    user_no=userNo,
                    temp_message_id=tempMessageId,
                )
                print(response)  # Display the response from send_message
            except Exception as e:
                print(f"Failed to send response to !test: {e}")
else:
    print("Login failed. Please check your credentials.")

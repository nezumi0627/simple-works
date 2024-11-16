# example.py

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from works.client import Works  # Import Works class

# Load environment variables
load_dotenv()

# Set the appropriate event loop policy for Windows platform
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Credentials from environment variables
input_id = os.getenv("INPUT_ID")
password = os.getenv("PASSWORD")
domain_id = int(os.getenv("DOMAIN_ID"))  # Convert to int
user_no = int(os.getenv("USER_NO"))  # Convert to int
temp_message_id = int(os.getenv("TEMP_MESSAGE_ID"))  # Convert to int

# Create cookie directory if it doesn't exist
COOKIE_DIR = Path("data")
COOKIE_DIR.mkdir(exist_ok=True)


# New function to handle sending all messages
def send_all_messages(
    client, channel_no, domain_id: int, user_no: int, temp_message_id: int
):
    """Send all types of messages in response to !sendall command."""
    # Send a normal message
    response = client.send_message(
        channel_no,
        "This is a test message from !sendall command.",
        domain_id=domain_id,
        user_no=user_no,
        temp_message_id=temp_message_id,
    )
    print(response)

    # Send a sticker
    sticker_response = client.send_sticker(
        group_id=channel_no,
        domain_id=domain_id,
        user_no=user_no,
        temp_message_id=temp_message_id,
        stk_type="line",
        package_id="18832978",  # Package ID
        sticker_id="485404830",  # Use sticker_id
    )
    print(sticker_response)

    # Send a custom log
    log_response = client.send_custom_log(
        channel_no,
        message="This is a custom log message.",
        button_message="Click Me",
        domain_id=domain_id,
        user_no=user_no,
        temp_message_id=temp_message_id,
    )
    print(log_response)

    # Send an additional log
    add_log_response = client.send_add_log(
        channel_no,
        input_id,
        domain_id,
        user_no,
        temp_message_id,
        user_name="Nezumi-Works - Free Multi-Function BOT",
        desc="Nezumi-Project2024",
        lang="ja",
        photo_hash="779911d9ab14b9caaec3fd44197a1adc",
    )
    print(add_log_response)


def main():
    """Main function to run the bot."""
    # Create an instance of the Works class
    client = Works(
        input_id=input_id,
        password=password,
        cookie_path=COOKIE_DIR / "./data/cookie.json",  # Specify cookie file path
    )

    # Message receiving process
    for message in client.receive_messages(domain_id, user_no):
        # Respond if the message content is "!test"
        content = message.get("content", "")
        channel_no = message.get("channelNo")

        if content == "!test":
            try:
                response = client.send_message(
                    channel_no,
                    "Hi!!",  # Response message
                    domain_id=domain_id,
                    user_no=user_no,
                    temp_message_id=temp_message_id,
                )
                print(response)  # Display the response from send_message
            except Exception as e:
                print(f"Failed to send response to !test: {e}")

        # Call all sending methods
        if content == "!sendall":
            try:
                send_all_messages(
                    client, channel_no, domain_id, user_no, temp_message_id
                )
            except Exception as e:
                print(f"Failed to send messages for !sendall: {e}")


if __name__ == "__main__":
    main()

# example.py

import asyncio
import sys

from works.client import Works  # Import Works class

# Set the appropriate event loop policy for Windows platform
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Credentials
input_id = "yusei@ncorp"
password = "n@20080627"
domainId = 400512308  # Works domain ID
userNo = 110002509504044  # Works bot account ID
tempMessageId = 733428260  # Temporary message ID (set as needed)

# Create an instance of the Works class
client = Works(input_id, password)


# New function to handle sending all messages
def send_all_messages(client, channel_no, domainId, userNo, tempMessageId):
    """Send all types of messages in response to !sendall command."""
    # Send a normal message
    response = client.send_message(
        channel_no,
        "This is a test message from !sendall command.",
        domain_id=domainId,
        user_no=userNo,
        temp_message_id=tempMessageId,
    )
    print(response)

    # Send a sticker
    sticker_response = client.send_sticker(
        group_id=channel_no,
        domain_id=domainId,
        user_no=userNo,
        temp_message_id=tempMessageId,
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
        domain_id=domainId,
        user_no=userNo,
        temp_message_id=tempMessageId,
    )
    print(log_response)

    # Send an additional log
    add_log_response = client.send_add_log(
        channel_no,
        input_id,
        domainId,
        userNo,
        tempMessageId,
        user_name="Nezumi-Works - Free Multi-Function BOT",
        desc="Nezumi-Project2024",
        lang="ja",
        photo_hash="779911d9ab14b9caaec3fd44197a1adc",
    )
    print(add_log_response)


# Message receiving process
for message in client.receive_messages(domainId, userNo):
    # Respond if the message content is "!test"
    content = message.get("content", "")
    channel_no = message.get("channelNo")

    if content == "!test":
        try:
            response = client.send_message(
                channel_no,
                "Hi!!",  # Response message
                domain_id=domainId,
                user_no=userNo,
                temp_message_id=tempMessageId,
            )
            print(response)  # Display the response from send_message
        except Exception as e:
            print(f"Failed to send response to !test: {e}")

    # Call all sending methods
    if content == "!sendall":
        try:
            send_all_messages(client, channel_no, domainId, userNo, tempMessageId)
        except Exception as e:
            print(f"Failed to send messages for !sendall: {e}")

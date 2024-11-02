# works/message_sender.py

import requests


def send_message(
    group_id: str,
    message: str,
    headers: dict,
    domain_id: str,
    user_no: str,
    temp_message_id: str,
) -> str:
    """
    Send a message to a specified group.

    Args:
        group_id (str): The ID of the group to send the message to.
        message (str): The content of the message.
        headers (dict): The headers to be used in the HTTP request.
        domain_id (str): The domain ID of the user.
        user_no (str): The user number.
        temp_message_id (str): Temporary message ID for the message.

    Returns:
        str: Success or error message.
    """
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
    payload = {
        "serviceId": "works",
        "channelNo": group_id,
        "tempMessageId": temp_message_id,
        "caller": {"domainId": domain_id, "userNo": user_no},
        "extras": "",
        "content": message,
        "type": 1,
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return "Message sent successfully!"
    else:
        return f"Error: Message sending failed. Status code: {response.status_code}"

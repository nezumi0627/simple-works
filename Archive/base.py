import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import csv
import json
import os
import random
import re
import sqlite3
import string
import subprocess
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Union

import requests
from g4f.client import Client

owners = [
    902100015957664,
    913000041624790,
    913000041325191,
    913000041775786,
    913000033734050,
    913000003889553,
    913000041941364,
    913000042405931,
    913000042616011,
    110002509263230,
    913000043047576,
    902100014853844,
    913000043260919,
]

debugger = 913000043047576
MaguRo = 902100014853844

domainId = 400512308
userNo = 110002509504044
tempMessageId = 733428260
level_id = 230000002301389
user_no_9 = 913000044300689

input_id = "yusei@ncorp"
password = "n@20080627"

LOGIN_URL = "https://auth.worksmobile.com/login/loginProcessV2"
LOGIN_PAGE_URL = (
    "https://auth.worksmobile.com/login/login?accessUrl=https://talk.worksmobile.com/"
)
Origin = "https://talk.worksmobile.com"


def login(input_id, password):
    """
    Login to Worksmobile service and return session cookies as a JSON string.
    Args:
        input_id (str): The account ID of the user.
        password (str): The password.
    Returns:
        str: The session cookies as a JSON string if login is successful,
             None if login fails.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"{LOGIN_PAGE_URL}&loginParam={input_id}",
        "Origin": Origin,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    try:
        login_page_response = requests.get(LOGIN_PAGE_URL, headers=headers)
        login_page_response.raise_for_status()
        payload = {
            "accessUrl": "https://talk.worksmobile.com/",
            "inputId": input_id,
            "password": password,
            "keepLoginYn": "N",
        }
        response = requests.post(
            LOGIN_URL, headers=headers, data=payload, allow_redirects=False
        )
        response.raise_for_status()
        cookies_dict = {cookie.name: cookie.value for cookie in response.cookies}
        cookies_json = json.dumps(cookies_dict, indent=4, ensure_ascii=False)
        return cookies_json
    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")
        return None


def cookies_to_header(cookies_dict):
    """
    クッキー辞書をCookieヘッダー文字列に変換します。
    引数:
        cookies_dict (dict): クッキーの辞書
    返値:
        str: Cookieヘッダーの値
    """
    return "; ".join(f"{name}={value}" for name, value in cookies_dict.items())


cookies_json = login(input_id, password)
if cookies_json:
    cookies_dict = json.loads(cookies_json)
    nheaders = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Cookie": cookies_to_header(cookies_dict),
    }


def get_status(date_str):
    """
    Fetch issue details from the specified URL with the timestamp of the given date.

    Args:
        date_str (str): The date string in the format 'YYYY-MM-DD'.

    Returns:
        list or str: A list of dictionaries containing content, status, and time,
                     or a message indicating no issues if none are found.
    """
    try:
        # Parse the date string and convert it to a timestamp
        date_time = datetime.strptime(date_str, "%Y-%m-%d")
        timestamp_ms = int(date_time.timestamp() * 1000)

        # Construct the API URL
        url = f"https://dashboard.worksmobile.com/jp/api/v2/issueDetail?date={timestamp_ms}&language=ja_JP"
        response = requests.get(url, headers=nheaders, timeout=30)

        # Check for successful response
        if response.status_code == 200:
            data = response.json()
            issues = data.get("data", [])

            if not issues:
                return "現在発生している問題はありません"

            results = []
            for issue in issues:
                contents = issue.get("contents", [])
                has_resolved = any(content.get("status") == 4 for content in contents)

                for content in contents:
                    status = content.get("status")
                    content_message = content.get("content")

                    # Determine status message
                    status_message = {1: "確認中", 2: "進行中", 4: "復旧完了"}.get(
                        status, "不明"
                    )

                    # Skip resolved issues if applicable
                    if has_resolved and status != 4:
                        continue

                    result = {
                        "コンテンツ": content_message,
                        "状態": status_message,
                    }

                    # Format the timestamp
                    timestamp_ms = content.get("time")
                    if timestamp_ms:
                        timestamp_s = timestamp_ms / 1000
                        formatted_date = datetime.fromtimestamp(
                            timestamp_s, tz=timezone.utc
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        result["発生時間"] = formatted_date
                    else:
                        result["発生時間"] = "不明"

                    results.append(result)

            if not results:
                return "現在発生している問題はありません"
            return results
        else:
            return f"エラー: ステータスコード {response.status_code}"

    except requests.RequestException as e:
        return f"リクエストエラー: {e}"


def initialize_db(db_path):
    """
    Initialize the SQLite database and create the messages table if it doesn't exist.
    Args:
        db_path (str): The path to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS received_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_no TEXT UNIQUE,
            channel_no TEXT,
            last_message_no INTEGER,
            message_time TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()


def receive_messages(headers, domainId, userNo, db_path="received_messages.db"):
    """
    Receive messages from the server and handle them.
    Args:
        headers (dict): The headers to be used in the HTTP request.
        domainId (str): The domain ID of the user.
        userNo (str): The user number.
        db_path (str): The path to the SQLite database.
    """
    initialize_db(db_path)
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/syncUserChannelList"
    payload = {
        "serviceId": "works",
        "userKey": {"domainId": domainId, "userNo": userNo},
        "filter": "none",
        "updatePaging": True,
        "pagingCount": 100,
        "userInfoCount": 10,
        "updateTime": int(time.time() * 1000),
        "beforeMsgTime": 0,
        "isPin": True,
        "requestAgain": False,
    }
    try:
        while True:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                handle_messages(response.json(), db_path)
            else:
                print(f"Error: Status code {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


def ack_message(channelNo, messageNo):
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/ackMessage"
    data = {
        "serviceId": "works",
        "messageNo": messageNo,
        "userNo": userNo,
        "channelNo": channelNo,
    }
    requests.post(url, headers=nheaders, data=json.dumps(data))


def searchSameChannel(hostid, targetid):
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/recommendChannel"
    payload = {
        "userNoList": [],
        "externalUserNoList": [hostid, targetid],
        "botNoList": [],
        "dlNoList": [],
        "groupNoList": [],
        "start": 0,
        "count": 100,
    }
    response = requests.post(url, headers=nheaders, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"HTTP Error: {response.status_code}")


def translate_text(text, target_language="ja"):
    """
    Sends a POST request to the translation API to translate text.
    Args:
        text (str): The text to be translated.
        target_language (str): The target language code (default is Japanese).
    Returns:
        str: The translated text, or a message if an error occurs.
    """
    url = "https://talk.worksmobile.com/p/translation/api/v1/translate"
    payload = {"target": [target_language], "format": "text", "text": [text]}
    try:
        response = requests.post(url, headers=nheaders, data=json.dumps(payload))
        response.raise_for_status()
        response_json = response.json()
        translated_text = response_json.get("translations", [{}])[0].get(
            "translatedText", ["No translation found"]
        )[0]
        return translated_text
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def load_unreact(filename):
    with open(filename, "r") as f:
        return json.load(f)


def get_channel_members(channel_no, member_update_time=0, paging_count=500):
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/getChannelMembers"
    payload = {
        "channelNo": channel_no,
        "memberUpdateTime": member_update_time,
        "pagingCount": paging_count,
    }
    response = requests.post(url, headers=nheaders, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_latest_image(channel_no, limit=100000, range_flag=3):
    url = (
        "https://talk.worksmobile.com/p/oneapp/client/chat/getContentMessageListByRange"
    )
    payload = {
        "baseMessageNo": 7,
        "channelNo": channel_no,
        "contentType": 1,
        "limit": limit,
        "rangeFlag": range_flag,
    }
    response = requests.post(url, headers=nheaders, json=payload)
    if response.status_code == 200:
        data = response.json()
        after_message_list = data.get("result", {}).get("afterMessageList", [])
        if not after_message_list:
            print("最新のメッセージが見つかりませんでした")
            return
        latest_message = after_message_list[-1]
        extras = json.loads(latest_message.get("extras", "{}"))
        resourcepath = extras.get("resourcepath", "")
        writer_id = latest_message.get("writerId", "")
        if not resourcepath:
            print("Resource path is missing in the message extras")
            return
        base_url = "https://talk.worksmobile.com/p/download"
        final_url = f"{base_url}{resourcepath}?channelNo={channel_no}&callerNo={writer_id}&ocn=1&serviceId=works"
        file_response = requests.get(final_url, headers=nheaders)
        if file_response.status_code == 200:
            file_name = resourcepath.split("/")[-1]
            with open(f"./ArchiveImages/{file_name}", "wb") as file:
                file.write(file_response.content)
            print(f"ファイルが正常にダウンロードされました: {file_name}")
            return file_name
        else:
            print(f"ファイルダウンロードエラー: {file_response.status_code}")
            print("レスポンスメッセージ:", file_response.text)
    else:
        print(f"Error: {response.status_code}")
        print("レスポンスメッセージ:", response.json())


def search_and_fetch_messages(
    keyword, start=0, display=1000, channel_no=291108891, msg_types=None
):
    """
    指定したチャンネルからキーワードに基づいてメッセージを検索・取得する関数。
    Args:
        keyword (str): 検索キーワード
        start (int): 取得開始位置（デフォルトは0）
        display (int): 取得するアイテム数（デフォルトは1000）
        channel_no (int): チャンネル番号（デフォルトは291108891）
        msg_types (str): メッセージタイプのリスト（デフォルトはNone）
    Returns:
        dict: レスポンスデータの辞書
    """
    if msg_types is None:
        msg_types = "1:3:4:5:6:7:8:10:11:12:13:14:16:17:19:22:23:24:25:26:27:28:29:30:37:39:44:46:47:48:49:96:97:98"
    timestamp = str(int(time.time() * 1000))
    payload = {
        "keyword": keyword,
        "start": start,
        "display": display,
        "channelNo": channel_no,
        "msgType": msg_types,
        "timeStamp": timestamp,
    }
    url = "https://talk.worksmobile.com/p/oneapp/client/search/searchChannel"
    response = requests.post(url, headers=nheaders, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def changeProfile(
    id,
    level_id,
    first_name,
    last_name,
    domain_id,
    org_name,
    account_id,
    private_email,
    messenger_type,
    messenger_content,
    birthday_content,
    photo_existence,
    level_name,
    authority_level,
    mobile_phone_country_code,
):
    url = f"https://admin.worksmobile.com/api/Z846869/contact/adminapi/v1/users/{id}"
    data = {
        "name": {
            "firstName": first_name,
            "lastName": last_name,
            "phoneticFirstName": "",
            "phoneticLastName": "",
        },
        "levelId": level_id,
        "i18nNames": [],
        "organizations": [
            {
                "domainId": domain_id,
                "represent": True,
                "name": org_name,
                "accountId": account_id,
                "orgUnits": [],
            }
        ],
        "aliasEmails": [],
        "privateEmail": private_email,
        "language": "ja_JP",
        "location": "",
        "messenger": {"type": messenger_type, "content": messenger_content},
        "birthday": {"calendarType": "S", "content": birthday_content},
        "relations": [],
        "id": id,
        "status": "NORMAL",
        "photoExistence": photo_existence,
        "levelName": level_name,
        "customFields": [],
        "useApp": True,
        "authorityLevel": authority_level,
        "tempId": False,
        "nickName": "",
        "workPhone": "",
        "mobilePhone": "",
        "mobilePhoneCountryCode": mobile_phone_country_code,
        "hiredDate": "",
        "task": "",
        "activationDate": "",
        "employeeNumber": "",
    }
    try:
        response = requests.put(url, headers=nheaders, data=json.dumps(data))
        if response.status_code == 204:
            print("Profile updated successfully.")
        else:
            print(f"Failed to update profile. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")


def getAllChats():
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/getVisibleUserChannelList"
    data = {
        "serviceId": "works",
        "userKey": {"domainId": domainId, "userNo": userNo},
        "filter": "none",
        "updatePaging": True,
        "pagingCount": 100,
        "userInfoCount": 10,
        "updateTime": 0,
        "beforeMsgTime": 0,
        "isPin": False,
        "requestAgain": False,
    }
    response = requests.post(url, headers=nheaders, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def getAllFriendsId():
    data = getAllChats()
    group_data = data.get("result", [])
    group_ids = []
    for group in group_data:
        if group.get("channelType") == 6:
            group_id = group.get("channelNo", "不明")
            group_ids.append(group_id)
    return group_ids


def getAllGroupsId():
    data = getAllChats()
    group_data = data.get("result", [])
    group_ids = []
    for group in group_data:
        if group.get("channelType") == 10:
            group_id = group.get("channelNo", "不明")
            group_ids.append(group_id)
    return group_ids


def format_friends(response):
    """
    友達データを指定された形式で整形し、リスト形式で表示する関数
    Parameters:
    response (dict): APIのレスポンスデータ。'result' キーに友達情報を含む辞書のリストがある。
    Returns:
    str: 整形された友達情報のリスト
    """
    friend_data = response.get("result", [])
    if not isinstance(friend_data, list):
        return f"エラー: 友達データはリストである必要があります。実際のデータ型: {type(friend_data)}"

    total_friends = 0
    formatted_friends = []

    for friend in friend_data:
        if not isinstance(friend, dict):
            return f"エラー: 各友達データは辞書である必要があります。実際のデータ型: {type(friend)}"

        try:
            # channelTypeが10の場合はスキップ
            if friend.get("channelType") == 10:
                continue

            user_list = friend.get("userList", [])
            # 名前と参加時間を取得
            user = next((user for user in user_list if isinstance(user, dict)), None)
            name = user.get("name", "不明") if user else "不明"
            join_time_ms = user.get("joinTime", "不明") if user else "不明"
            channel_no = friend.get("channelNo", "不明")
            user_no = friend.get("userNo", "不明")

            # 日付に変換
            if join_time_ms != "不明":
                join_time_dt = datetime.fromtimestamp(join_time_ms / 1000)
                join_time_str = join_time_dt.strftime("%Y-%m-%d %H:%M")
            else:
                join_time_str = "不明"

            message_time_ms = friend.get("messageTime", "不明")
            if message_time_ms != "不明":
                message_time_dt = datetime.fromtimestamp(message_time_ms / 1000)
                message_time_str = message_time_dt.strftime("%Y-%m-%d %H:%M")
            else:
                message_time_str = "不明"

            formatted_friends.append(
                f"""------------------
名前: {name}
Channel ID: {channel_no}
user No : {user_no}
追加時間: {join_time_str}
最終更新時間: {message_time_str}"""
            )
            total_friends += 1

        except Exception as e:
            return f"エラー: データの整形中に問題が発生しました。詳細: {e}"

    result = f"[All Friends]\n\n合計友達数: {total_friends}\n" + "\n".join(
        formatted_friends
    )
    return result


def format_join_groups(response):
    """
    グループデータを指定された形式で整形し、リスト形式で表示する関数
    Parameters:
    response (dict): APIのレスポンスデータ。'result' キーにグループ情報を含む辞書のリストがある。
    Returns:
    str: 整形されたグループ情報のリスト
    """
    group_data = response.get("result", [])
    if not isinstance(group_data, list):
        return f"エラー: グループデータはリストである必要があります。実際のデータ型: {type(group_data)}"
    total_groups = 0
    formatted_groups = []
    for group in group_data:
        if not isinstance(group, dict):
            return f"エラー: 各グループデータは辞書である必要があります。実際のデータ型: {type(group)}"
        try:
            if group.get("channelType") == 10:
                title = group.get("title", "不明")
                channel_no = group.get("channelNo", "不明")
                user_count = group.get("userCount", "不明")
                message_time = group.get("messageTime", "不明")
                format_message_time = message_time / 1000.0
                dt = datetime.fromtimestamp(format_message_time)
                formatted_groups.append(
                    f"""------------------
グループ名:\n{title}
グループID: {channel_no}
参加人数: {user_count}
最終更新時間: {dt.strftime('%Y-%m-%d %H:%M')}"""
                )
                total_groups += 1
        except Exception as e:
            return f"エラー: データの整形中に問題が発生しました。詳細: {e}"
    result = f"[All Join Groups]\n\n合計参加数: {total_groups}\n" + "\n".join(
        formatted_groups
    )
    return result


def get_read_infos(channel_no):
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/getReadInfos"
    payload = {"channelNo": channel_no, "serviceId": "works"}
    try:
        response = requests.post(url, headers=nheaders, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            print("エラー: ステータスコード:", response.status_code)
            return {}
    except requests.RequestException as e:
        print("リクエストエラー:", e)
        return {}


def extract_info(response_data):
    messages = response_data.get("result", [])
    if not messages:
        return "メッセージがありません。"
    total_count = len(messages)
    if total_count == 0:
        return "メッセージがありません。"
    first_time = min(message["messageUnixTime"] for message in messages)
    last_time = max(message["messageUnixTime"] for message in messages)
    name_counts = {}
    for message in messages:
        name = message["name"]
        name_counts[name] = name_counts.get(name, 0) + 1
    first_time_str = datetime.fromtimestamp(first_time).strftime("%Y-%m-%d %H:%M:%S")
    last_time_str = datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M:%S")
    name_summary = "\n".join(
        f"{name}: 合計 {count} 回\n" for name, count in name_counts.items()
    )
    return (
        f"総受信回数: {total_count} 回\n\n"
        f"一番最初に送られた時間:\n{first_time_str}\n\n"
        f"最後に送られた時間:\n{last_time_str}\n\n"
        f"------------------\n{name_summary}"
    )


def create_account(input_name, domainId, level_id, nheaders):
    create_account_url = (
        "https://admin.worksmobile.com/api/Z846869/contact/adminapi/v1/users"
    )
    random_number = "".join(random.choices(string.digits, k=6))
    account_id = "nezumi" + random_number
    name = input_name[:80]
    half_length = len(name) // 2
    if len(name) % 2 == 0 and half_length <= 40:
        last_name = name[:half_length]
        first_name = name[half_length:]
    else:
        last_name = name[:-1]
        first_name = name[-1:]
    payload = {
        "organizations": [
            {
                "domainId": domainId,
                "accountId": account_id,
                "externalKey": "",
                "orgUnits": [],
                "represent": True,
            }
        ],
        "name": {
            "firstName": first_name,
            "lastName": last_name,
            "phoneticFirstName": "",
            "phoneticLastName": "",
        },
        "levelId": level_id,
        "passwordCreation": "AUTO",
        "mobilePhoneCountryCode": "+81",
        "language": "ja_JP",
        "aliasEmails": [],
        "birthday": {"calendarType": "S", "content": ""},
        "deletedPhoto": False,
        "employmentTypeId": 0,
        "hiredDate": "",
        "i18nNames": [],
        "invitationEmail": "",
        "location": "",
        "messenger": {"content": "", "customType": "", "type": ""},
        "mobilePhone": "",
        "nickName": "",
        "password": "",
        "photoPath": "",
        "privateEmail": "",
        "relations": [],
        "task": "",
        "workPhone": "",
        "activationDate": "",
        "employeeNumber": "",
        "changePasswordAtNextLogin": True,
    }
    response_create_account = requests.post(
        create_account_url, headers=nheaders, json=payload
    )
    user_key_list = []
    if response_create_account.status_code == 201:
        user_no = response_create_account.json()["id"]
        user_key_list.append({"domainId": domainId, "userNo": user_no})
        print("User No:", user_no)
    else:
        print(
            f"Failed to create account. Status Code: {response_create_account.status_code}, "
            f"Response: {json.dumps(response_create_account.json(), indent=4, ensure_ascii=False)}"
        )
    return user_key_list


def check_speed(group_id, message, domain_id=domainId, user_no=userNo):
    """
    Send a message to a specified group.
    Args:
        group_id (int): The ID of the group.
        message (str): The message to be sent.
        domain_id (int, optional): The domain ID of the caller. Defaults to None.
        user_no (int, optional): The user number of the caller. Defaults to None.
    Returns:
        float: The time taken to send the message in seconds.
    """
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
    payload = {
        "serviceId": "works",
        "channelNo": group_id,
        "tempMessageId": tempMessageId,
        "caller": {"domainId": domain_id, "userNo": user_no},
        "extras": "",
        "content": message,
        "type": 1,
    }

    start_time = time.time()  # 計測開始

    response = requests.post(url, headers=nheaders, json=payload)

    end_time = time.time()  # 計測終了
    elapsed_time = end_time - start_time  # 経過時間

    if response.status_code == 200:
        print("メッセージの送信に成功しました！")
    else:
        print("メッセージの送信に失敗しました。ステータスコード:", response.status_code)

    return elapsed_time  # 経過時間を返す


def send_message(group_id, message, domain_id=domainId, user_no=userNo):
    """
    Send a message to a specified group.
    Args:
        group_id (int): The ID of the group.
        message (str): The message to be sent.
        domain_id (int, optional): The domain ID of the caller. Defaults to None.
        user_no (int, optional): The user number of the caller. Defaults to None.
    """
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
    payload = {
        "serviceId": "works",
        "channelNo": group_id,
        "tempMessageId": tempMessageId,
        "caller": {"domainId": domain_id, "userNo": user_no},
        "extras": "",
        "content": message,
        "type": 1,
    }
    response = requests.post(url, headers=nheaders, json=payload)
    if response.status_code == 200:
        print("メッセージの送信に成功しました！")
    else:
        print("メッセージの送信に失敗しました。ステータスコード:", response.status_code)


def send_sticker(
    group_id,
    stkType,
    package_id,
    sticker_id,
    stkOpt="",
):
    """
    Send a message to a specified group.
    Args:
        group_id (int): The ID of the group.
        stkType (str): The type of the sticker.
        package_id (str): The ID of the sticker package.
        sticker_id (str): The ID of the sticker.
        stkOpt (str, optional): The sticker options.
    """
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
    extras = {
        "channelNo": group_id,
        "pkgVer": "3",
        "pkgId": package_id,
        "stkId": sticker_id,
        "stkType": stkType,
        "stkOpt": stkOpt,
    }
    payload = {
        "serviceId": "works",
        "channelNo": group_id,
        "tempMessageId": tempMessageId,
        "caller": {"domainId": domainId, "userNo": userNo},
        "extras": json.dumps(extras),
        "type": 18,
    }
    response = requests.post(url, headers=nheaders, json=payload)
    if response.status_code == 200:
        print("メッセージの送信に成功しました！")
    else:
        print("メッセージの送信に失敗しました。ステータスコード:", response.status_code)


def get_works_member():
    url = "https://admin.worksmobile.com/api/Z846869/contact/adminapi/v1/users"
    params = {
        "includeStatusDetail": "true",
        "maxResults": 100,
        "includeSubOrgUnitMembers": "true",
        "page": 1,
        "status": "ALL",
        "sortField": "POSITION",
        "sortOrder": "ASC",
    }

    response = requests.get(url, params=params, headers=nheaders)

    if response.status_code == 200:
        return response.json()  # JSONレスポンスを返す
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


def del_member(user_id):
    url = (
        f"https://admin.worksmobile.com/api/Z846869/contact/adminapi/v1/users/{user_id}"
    )

    response = requests.delete(url, headers=nheaders)

    if response.status_code == 204:
        print("ユーザーの削除に成功しました。")
    else:
        print(f"削除に失敗しました。ステータスコード: {response.status_code}")


def member_resign(user_ids):
    url = "https://admin.worksmobile.com/api/Z846869/contact/adminapi/v1/users/resign"

    # ユーザーIDをJSON形式に変換
    data = json.dumps(user_ids)

    response = requests.post(url, headers=nheaders, data=data)

    if response.status_code == 204:
        print("ユーザーが正常に退会されました。")
    else:
        print(f"Error: {response.status_code}, {response.text}")


def send_custom_log(
    group_id,
    Message,
    buttonMessage,
    buttonUrl="https://github.com/nezumi0627",
):
    """
    Send a join log message to a specified group.
    Args:
        group_id (int): The ID of the group.
    """
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
    payload = {
        "serviceId": "works",
        "channelNo": group_id,
        "tempMessageId": tempMessageId,
        "caller": {"domainId": domainId, "userNo": userNo},
        "extras": {
            "text": buttonMessage,
            "url": buttonUrl,
        },
        "content": Message,
        "type": 30,
    }
    payload["extras"] = json.dumps(payload["extras"])
    response = requests.post(url, data=json.dumps(payload), headers=nheaders)
    if response.status_code == 200:
        print("メッセージの送信に成功しました！")
    else:
        print("メッセージの送信に失敗しました。ステータスコード:", response.status_code)


def shere_message(original_channel_no, original_message_no, target_channel_no):
    url = "https://talk.worksmobile.com/gquery"
    data = {
        "operationName": "qy",
        "variables": {
            "forwardMessages": [
                {
                    "tid": random.randint(1000000000, 9999999999),
                    "source": {
                        "channelNo": original_channel_no,
                        "messageNo": original_message_no,
                    },
                    "target": {"channelNo": target_channel_no, "needSleep": False},
                }
            ]
        },
        "query": """
            query qy(
                $forwardMessages: [param_forward_message!]!
            ) {
                batch_forward_message(
                    forwardMessages: $forwardMessages
                ) {
                    message
                    result
                    error
                }
            }
        """,
    }

    response = requests.post(url, headers=nheaders, json=data)

    return response.status_code, response.text


def get_member_data(user_id_no: str):
    url = f"https://admin.worksmobile.com/api/public/admin/function-auth/mixed/MF002/members/{user_id_no}"

    response = requests.get(url, headers=nheaders)
    response.raise_for_status()
    return response.json()


def send_add_log(group_id):
    """
    Send a user addition log message to a specified group.
    Args:
        group_id (int): The ID of the group.
    """
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/sendMessage"
    payload = {
        "serviceId": "works",
        "channelNo": group_id,
        "tempMessageId": tempMessageId,
        "caller": {"domainId": domainId, "userNo": userNo},
        "extras": {
            "account": input_id,
            "userName": "ねずわーくす - 無料多機能BOT",
            "desc": "Nezumi-Project2024",
            "lang": "ja",
            "photoHash": "779911d9ab14b9caaec3fd44197a1adc",
        },
        "type": 26,
    }
    payload["extras"] = json.dumps(payload["extras"])
    response = requests.post(url, data=json.dumps(payload), headers=nheaders)
    if response.status_code == 200:
        print("メッセージの送信に成功しました！")
    else:
        print("メッセージの送信に失敗しました。ステータスコード:", response.status_code)


def invite_user(group_id, user_id, domain_id1=0):
    """ユーザーを招待する関数
    Args:
        group_id (str): グループID
        user_id (str): ユーザーID
        domain_id (int, optional): ドメインID。指定がない場合はデフォルトの0が使用されます
        inviter_domain_id (int, optional): 招待者のドメインID。指定がない場合はNoneが使用されます
        inviter_user_no (str, optional): 招待者のユーザーID。指定がない場合はNoneが使用されます
    """
    payload = {
        "channelNo": group_id,
        "channelType": 10,
        "botNoList": [],
        "userKeyList": [{"domainId": domain_id1, "userNo": user_id}],
        "dlNoList": [],
        "groupNoList": [],
        "requestService": "",
        "description": "undefined",
        "inviter": {
            "domainId": domainId,
            "userNo": userNo,
        },
    }
    response = requests.post(
        "https://talk.worksmobile.com/p/oneapp/client/chat/join",
        headers=nheaders,
        json=payload,
    )
    if response.status_code == 200:
        print("ユーザーの招待に成功しました。")
    else:
        print(f"ユーザーの招待に失敗しました: {response.text}")


def create_group(name, hostUserNo, inviteUserNo):
    payload = {
        "channelNo": 0,
        "channelType": 7,
        "botNoList": [],
        "userKeyList": [
            {"domainId": 0, "userNo": inviteUserNo},
            {"domainId": 0, "userNo": hostUserNo},
        ],
        "dlNoList": [],
        "groupNoList": [],
        "requestService": "",
        "title": name,
        "photoPath": "",
        "description": "",
        "sendExcludeMemberSystemMsg": True,
        "inviter": {"domainId": domainId, "userNo": userNo},
    }
    response = requests.post(
        "https://talk.worksmobile.com/p/oneapp/client/chat/join",
        headers=nheaders,
        json=payload,
    )
    if response.status_code == 200:
        print("グループを作成しました: ", name)
    else:
        print("グループの作成に失敗しました: ", name)


def leave_group(group_id):
    """
    Leave a group with the given group ID.
    Args:
        group_id (int): The ID of the group to leave.
    Returns:
        None
    """
    payload = {
        "channelNo": 0,
        "channelNoList": [group_id],
    }
    response = requests.post(
        "https://talk.worksmobile.com/p/oneapp/client/chat/quit",
        headers=nheaders,
        json=payload,
    )
    if response.status_code == 200:
        print("グループを退出しました: ", group_id)
    else:
        print("グループの退出に失敗しました: ", group_id)


def getUserInfo(userNo):
    params = {"domainId": 0, "client": "PC_WEB"}
    getUserInfoBase = "https://talk.worksmobile.com/p/contact/v4/users/"
    getUserInfoUrl = getUserInfoBase + str(userNo)
    try:
        user_response = requests.get(getUserInfoUrl, headers=nheaders, params=params)
        if user_response.status_code == 200:
            user_info = user_response.json()
            return user_info
        else:
            print(
                "ユーザー情報を取得できませんでした。ステータスコード:",
                user_response.status_code,
            )
            return {}
    except requests.RequestException as e:
        print("ユーザー情報の取得中にエラーが発生しました:", e)
        return {}


def get_channel_info(channel_no):
    url = "https://talk.worksmobile.com/p/oneapp/client/chat/getChannelInfo"
    payload = {
        "channelNo": str(channel_no),
        "direction": "0",
        "messageNo": "0",
        "recentMessageCount": "0",
    }
    response = requests.post(url, json=payload, headers=nheaders)
    if response.status_code == 200:
        response_data = response.json()
        channel_info = response_data.get("channelInfo", {})
        return channel_info
    else:
        print("エラーが発生しました:", response.status_code)
        return None


def shutdown(group_id):
    send_message(group_id, "PCをシャットダウンします...")
    subprocess.run(["shutdown", "/s", "/t", "0"])


def restart(group_id):
    """Restarts the current program."""
    try:
        send_message(group_id, "プログラムを再起動します。")
        subprocess.Popen([rf"{os.getcwd()}\\restart.bat"])
    except Exception as e:
        print(f"エラーが発生しました: {e}")


def stop(group_id):
    """Stops the current program."""
    send_message(group_id, "プログラムを停止します。")
    sys.exit()


image_generation_models = ["playground-v2.5", "sdxl-lightning", "stable-diffusion-3"]
text_generation_models = [
    "gemma-2-9b",
    "gemma-2-27b",
    "gpt-3.5-turbo",
    "gpt-4o-mini",
    "gpt-4o",
    "llama-3-70b-instruct",
    "mixtral-8x7b",
    "SparkDesk-v1.1",
]


def gen_ai(
    model_type: str, model_name: str, content: str, save_dir: str
) -> Union[str, None]:
    if model_type == "image" and model_name not in image_generation_models:
        raise ValueError(f"Invalid image generation model: {model_name}")
    if model_type == "text" and model_name not in text_generation_models:
        raise ValueError(f"Invalid text generation model: {model_name}")

    def serialize_choice(choice: Any) -> Dict[str, Any]:
        try:
            return {
                "text": getattr(choice, "text", None),
                "index": getattr(choice, "index", None),
                "logprobs": getattr(choice, "logprobs", None),
                "finish_reason": getattr(choice, "finish_reason", None),
            }
        except Exception as e:
            return {"error": str(e)}

    def serialize_response(response: Any) -> Dict[str, Any]:
        try:
            if isinstance(response, list):
                return [serialize_response(item) for item in response]
            elif isinstance(response, dict):
                return {k: serialize_response(v) for k, v in response.items()}
            elif hasattr(response, "__dict__"):
                return {k: serialize_response(v) for k, v in vars(response).items()}
            else:
                return response
        except Exception as e:
            return {"error": str(e)}

    fails_dir = os.path.join(save_dir, "fails")
    os.makedirs(fails_dir, exist_ok=True)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": content}],
        )
        response_data = {
            "complete_response": serialize_response(response),
            "choices": [serialize_choice(choice) for choice in response.choices],
            "usage": serialize_response(response.usage),
        }
        answers_dir = os.path.join(save_dir, "answers")
        os.makedirs(answers_dir, exist_ok=True)
        file_path = os.path.join(answers_dir, f"{model_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
        if model_type == "image":
            content_text = (
                response_data.get("complete_response", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            urls = [
                line.split("](")[-1].split(")")[0]
                for line in content_text.split("\n")
                if line.startswith("[![")
            ]
            if urls:
                return urls[0]
        elif model_type == "text":
            content_text = (
                response_data.get("complete_response", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return content_text
        else:
            raise ValueError("Invalid model type. Use 'image' or 'text'.")
    except Exception as e:
        error_message = str(e)
        error_data = {"model": model_name, "error": error_message}
        error_file_path = os.path.join(fails_dir, f"{model_name}_fail.json")
        with open(error_file_path, "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)
        print(f"Saved error for model '{model_name}' to '{error_file_path}'")
        return None


def upload_file(file_path):
    """
    Upload a file to PythonAnywhere.
    :param file_path: Local path of the file to upload
    """
    file_name = os.path.basename(file_path)
    upload_path = f"/home/nezuminff0627/mysite/imagefiles/{file_name}"
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/nezuminff0627/files/path{upload_path}"
    token = "3e13aa72810ad2537b54a3c8f3b16edc8f81adb4"
    headers = {"Authorization": f"Token {token}"}
    files = {"content": open(file_path, "rb")}
    try:
        requests.post(upload_url, headers=headers, files=files)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    finally:
        files["content"].close()


client = Client()


def initialize_csv(file_name):
    """
    Initialize the CSV file with the header if it does not exist.

    Args:
        file_name (str): The path to the CSV file.
    """
    header = [
        "channel_no",
        "message_no",
        "user_no",
        "message_time",
        "content",
        "extras",
    ]
    if not os.path.isfile(file_name):
        with open(file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header)


def record_message_csv(
    file_name, channel_no, message_no, user_no, message_time, content, extras
):
    """
    Record a message to the CSV file.

    Args:
        file_name (str): The path to the CSV file.
        channel_id (str): The channel ID.
        message_no (int): The message number.
        channel_no (int): The channel number.
        last_message_no (int): The last message number.
        message_time (str): The time of the message.
        content (str): The content of the message.
        extras (str): Additional data related to the message.
    """
    # 改行を\nに変換
    content = content.replace("\n", "\\n")
    extras = extras.replace("\n", "\\n")

    with open(file_name, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [channel_no, message_no, user_no, message_time, content, extras]
        )


def create_default_config(channel_id):
    """
    Create a default configuration file for the channel if it doesn't exist.

    Args:
        channel_id (str): The channel ID.
    """
    config = {
        "send_stickers": True,  # デフォルトでスタンプ送信を有効
        "send_url_info": True,  # デフォルトでURL情報送信を有効
    }
    with open(f"./config/{channel_id}.json", "w") as config_file:
        json.dump(config, config_file, indent=4)


def load_config(channel_id):
    """
    Load the configuration file for the specified channel.

    Args:
        channel_id (str): The channel ID.

    Returns:
        dict: The configuration for the channel.
    """
    config_path = f"./config/{channel_id}.json"
    if not os.path.exists(config_path):
        create_default_config(channel_id)
    with open(config_path, "r") as config_file:
        return json.load(config_file)


def save_config(channel_id, config):
    """
    Save the configuration file for the specified channel.

    Args:
        channel_id (str): The channel ID.
        config (dict): The configuration to save.
    """
    with open(f"./config/{channel_id}.json", "w") as config_file:
        json.dump(config, config_file, indent=4)


BOARD_DIR = "./board/"  # 掲示板のJSONファイルを保存するディレクトリ


def add_board(content, channel_no, name, member_count, user_no, user_name):
    if len(content) > 50:
        return "エラー: 一言は50文字以内で入力してください。"

    board_data = {
        "channel_no": channel_no,
        "name": name,  # グループ名を追加
        "user_no": user_no,  # ユーザー番号を追加
        "user_name": user_name,  # ユーザー名を追加
        "member_count": member_count,
        "added_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": content,
    }

    # ファイル名はchannel_no.json
    file_path = os.path.join(BOARD_DIR, f"{channel_no}.json")

    # 新しい掲示板エントリを追加
    # 既存のデータがある場合は削除
    if os.path.exists(file_path):
        os.remove(file_path)

    # 新しいデータを作成して保存
    data = {"boards": [board_data]}  # 新規データを作成

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return "掲示板に追加しました。"


# 掲示板を表示する関数
def show_boards():
    result = "掲示板一覧:\n"
    found_any_boards = False  # 掲示板が見つかったかを追跡するフラグ

    # BOARD_DIR ディレクトリ内のすべてのJSONファイルを探索
    for file_name in os.listdir(BOARD_DIR):
        if file_name.endswith(".json"):
            file_path = os.path.join(BOARD_DIR, file_name)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("boards"):  # ボードデータが存在するか確認
                found_any_boards = True
                for board in data["boards"]:
                    result += (
                        f"------======------\n"
                        f"グループ番号:\n{board['channel_no']}\n"  # グループ番号
                        f"グループ名:\n{board['name']}\n"  # グループ名
                        f"ひとこと:\n\n{board['message']}\n\n"  # 一言
                        f"追加した人の名前:\n{board['user_name']}\n"  # ユーザー名
                        f"掲示板追加時間:\n{board['added_time']}\n\n"  # 追加時間
                    )

    if not found_any_boards:
        return "掲示板は存在しません。"

    return result


# 掲示板から削除する関数
def del_board(channel_no, index):
    file_path = os.path.join(BOARD_DIR, f"{channel_no}.json")
    if not os.path.exists(file_path):
        return "掲示板は存在しません。"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if index < 1 or index > len(data["boards"]):
        return "エラー: 指定された掲示板番号は無効です。"

    # 指定したインデックスの掲示板を削除
    del data["boards"][index - 1]

    # 再度ファイルに保存
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return "掲示板を削除しました。"


def join_board(channel_no, user_no, user_info):
    file_path = os.path.join(BOARD_DIR, f"{channel_no}.json")
    if not os.path.exists(file_path):
        return "掲示板は存在しません。"

    # ファイルを読み込むが、データは使用しない
    with open(file_path, "r", encoding="utf-8") as f:
        json.load(f)  # データを読み込むが使用しないため、変数に代入しない

    participant_message = (
        f"掲示板から参加しました\n\n"
        f"名前: {user_info.get('name', {}).get('displayName')}\n"
        f"ID: {user_info.get('userId')}\n\n"
        f"申請時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # ユーザーを招待する処理
    invite_user(group_id=str(channel_no), user_id=str(user_no))

    return participant_message


def add_unreact_user(id):
    # 無視リストのファイルパス
    unreact_file = "unreact_users.json"

    try:
        # ファイルが存在すれば読み込む
        with open(unreact_file, "r") as f:
            unreact_users = json.load(f)
            # リストでない場合は空のリストを作成
            if not isinstance(unreact_users, list):
                unreact_users = []
    except FileNotFoundError:
        # ファイルが存在しなければ空のリストを作成
        unreact_users = []

    # リストにユーザーIDを追加（重複を避けるためにチェック）
    if id not in unreact_users:
        unreact_users.append(id)

    # ファイルに書き込む
    with open(unreact_file, "w") as f:
        json.dump(unreact_users, f)


def load_unreact_users():
    # 無視リストのファイルパス
    unreact_file = "unreact_users.json"

    try:
        # ファイルが存在すれば読み込む
        with open(unreact_file, "r") as f:
            unreact_users = json.load(f)
            # リストでない場合は空のリストを返す
            if not isinstance(unreact_users, list):
                return []
            return unreact_users  # IDのリストを返す
    except FileNotFoundError:
        # ファイルが存在しなければ空のリストを返す
        return []


def handle_messages(messages, db_path="received_messages.db"):
    """
    Handle received messages and record them in the SQLite database.

    Args:
        messages (dict): The received messages.
        db_path (str): The path to the SQLite database.
    """
    if not isinstance(messages, dict):
        print("Received messages are not a dictionary.")
        return

    results = messages.get("result", [])
    unreact_users = load_unreact_users()  # ここで無視リストを読み込む

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for message in results:
        if not isinstance(message, dict):
            print(f"Error: Message is not a dictionary: {message}")
            continue

        last_message_no = int(message.get("lastMessageNo", 0))
        message_time = message.get("messageTime", "Unknown")
        message_no = message.get("messageNo")
        user_no = message.get("userNo")
        content = message.get("content", "")
        channel_no = message.get("channelNo")
        extras = message.get("extras", "{}")

        # user_no_9 と unreact_users をチェック
        if user_no == user_no_9 and user_no in unreact_users:
            continue

        # Check if the message is already in the database
        cursor.execute(
            "SELECT COUNT(*) FROM received_messages WHERE message_no=?", (message_no,)
        )
        if cursor.fetchone()[0] > 0:
            continue

        # Insert message into SQLite database
        try:
            cursor.execute(
                """
                INSERT INTO received_messages (message_no, channel_no, last_message_no, message_time, content)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    message_no,
                    channel_no,
                    last_message_no,
                    message_time,
                    json.dumps(message),
                ),
            )
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            continue

        # Handle extras (stickers and URL info)
        config = load_config(channel_no)
        send_stickers = config.get("send_stickers", True)
        send_url_info = config.get("send_url_info", True)

        try:
            if user_no == user_no_9 and user_no in unreact_users:
                pass
            if extras:
                extras_dict = json.loads(extras)

                # Process sticker information
                if send_stickers:
                    pkg_id = extras_dict.get("pkgId")
                    stk_id = extras_dict.get("stkId")
                    stk_type = extras_dict.get("stkType")
                    stk_opt = extras_dict.get("stkOpt")
                    if stk_type and pkg_id and stk_id:
                        send_sticker(channel_no, stk_type, pkg_id, stk_id, stk_opt)

                # Process URL information
                if send_url_info:
                    urlcontent = extras_dict.get("content", {})
                    og_title = urlcontent.get("ogTitle", "No Title")
                    og_desc = urlcontent.get("ogDesc", "No Description")
                    og_url = urlcontent.get("ogUrl", None)
                    if og_url:
                        message_text = f"[URL INFO]\n\nTitle:\n{og_title}\n\nDescription:\n{og_desc}\n\n"
                        send_message(channel_no, message_text)

            if content.startswith("sticker:"):
                arg = content[len("sticker:") :].strip()
                if arg.lower() == "on":
                    config["send_stickers"] = True
                    save_config(channel_no, config)
                    send_message(channel_no, "スタンプを真似します")
                elif arg.lower() == "off":
                    config["send_stickers"] = False
                    save_config(channel_no, config)
                    send_message(channel_no, "スタンプの送信をOFFにしました")

            # URL INFO送信のON/OFF コマンド
            if content.startswith("urlinfo:"):
                arg = content[len("urlinfo:") :].strip()
                if arg.lower() == "on":
                    config["send_url_info"] = True
                    save_config(channel_no, config)
                    send_message(channel_no, "URLの詳細を送信します")
                elif arg.lower() == "off":
                    config["send_url_info"] = False
                    save_config(channel_no, config)
                    send_message(channel_no, "URLの詳細送信をOFFにしました")

            if content.startswith("unreact:"):
                _, user_id = content.split(":")  # コロンで分割
                try:
                    user_id = int(user_id)
                    add_unreact_user(user_id)  # ユーザーを無視リストに追加
                    send_message(channel_no, f"{user_id}を無視リストに入れました")
                except ValueError:
                    send_message(channel_no, "Invalid user ID format.")

            if content == "help":
                try:
                    with open("./help.txt", "r", encoding="utf-8") as f:
                        help_text = f.read()

                    if user_no == debugger:
                        # デバッガの場合は全コマンドを表示
                        pass
                    else:
                        # デバッガ以外の場合は基本コマンドのみ表示
                        basic_commands_end = help_text.find("開発者専用コマンド:")
                        if basic_commands_end != -1:
                            help_text = help_text[:basic_commands_end].strip()

                    send_message(channel_no, help_text)
                except FileNotFoundError:
                    print("エラー: help.txt が見つかりませんでした。")
                except Exception as e:
                    print(f"エラー: help.txt の読み取りに失敗しました: {e}")

            if content == "sync":
                if user_no == debugger:
                    ids = getAllGroupsId()
                    for id in ids:
                        ack_message(id, 10000)
                    send_message(channel_no, "receiveの同期を完了しました")
                else:
                    pass

            if content == "fhelp":
                with open("./flex_help.txt", "r", encoding="utf-8") as f:
                    help_text = f.read()
                send_custom_log(channel_no, help_text, "help-Message")

            if content == "checkno":
                send_message(channel_no, f"{message_no}")

            if content == "test":
                send_message(channel_no, "ok, I'm works !!")

            if content == "mid":
                send_message(channel_no, f"{user_no}")

            if content == "sp":
                # メッセージ送信の計測
                elapsed_time_send = check_speed(channel_no, "...")

                # プロフィール取得の計測
                start_time_profile = time.time()
                user_info = getUserInfo(user_no)
                elapsed_time_profile = time.time() - start_time_profile

                # グループ情報取得の計測
                start_time_group = time.time()
                channel_infos = get_channel_info(channel_no)
                elapsed_time_group = time.time() - start_time_group

                # 結果を送信
                result_message = (
                    f"Send Message: {elapsed_time_send:.2f}秒\n"
                    f"Get User: {elapsed_time_profile:.2f}秒\n"
                    f"Get Group: {elapsed_time_group:.2f}秒"
                )
                send_message(channel_no, result_message)

            if content.startswith("usearch:"):
                id = content[len("usearch:") :].strip()
                user_data = getUserInfo(id)
                if user_data is None:
                    send_message(channel_no, "ユーザー情報が見つかりませんでした")
                    continue
                displayName = user_data.get("name", {}).get("displayName") or None
                photoUrl = user_data.get("photo", {}).get("photoUrl") or None
                serviceType = user_data.get("worksAt", {}).get("serviceType") or None
                send_message(
                    channel_no,
                    f"Name: {displayName}\nUrl: {photoUrl}\nserviceType: {serviceType}",
                )

            if content == "権限":
                if user_no == MaguRo:
                    send_message(
                        channel_no, "えっと...たしかあなたまぐろさんですよね!!🐟️"
                    )
                elif user_no == debugger:
                    send_message(channel_no, "あなたは開発者です🕶️")
                elif int(user_no) in owners:
                    send_message(channel_no, f"{user_no} >>> \nあなたは権限者です")
                else:
                    send_message(channel_no, "あなたは権限者ではありません")

            if content == "me":
                me_id = user_no
                if me_id == MaguRo:
                    title = "権限: [お魚研究家🐟️]"
                elif me_id == debugger:
                    title = "権限: [開発者]"
                elif me_id in owners:
                    title = "権限: [OWNER]"
                else:
                    title = "権限: [USER]"
                userInfoo = getUserInfo(me_id)
                if userInfoo is not None:
                    msg = (
                        f"{title}\n\n"
                        f"ID :{userInfoo.get('userId', None)}\n"
                        f"名前 :{userInfoo.get('name', {}).get('displayName', None)}\n"
                        f"アイコン :\n{userInfoo.get('photo', {}).get('photoUrl', None)}"
                    )
                    send_message(channel_no, msg)
                else:
                    send_message(channel_no, "ユーザー情報を取得できませんでした。")

            if content.startswith("samegroup:"):
                try:
                    targetid = int(content.split(":")[1])
                    data = searchSameChannel(user_no, targetid)
                    channel_list = data.get("channelList", [])
                    msg = "[searchSameGroup]\n"
                    for channel in channel_list:
                        msg += (
                            f"グループ名:\n{channel['title']}\n"
                            f"グループID: {channel['channelNo']}\n"
                            f"参加人数: {channel['memberCount']}\n"
                            "----------------------------\n"
                        )
                    send_message(channel_no, msg)
                except Exception as e:
                    print(f"Error: {e}")

            if content.startswith("send:"):
                try:
                    parts = content.split(":", 2)
                    if len(parts) < 3:
                        print("Error: Message format is incorrect.")
                        return
                    num = int(parts[1])
                    text = parts[2]
                    if user_no == debugger:
                        for _i in range(num):
                            send_message(channel_no, text)
                    else:
                        pass
                except ValueError:
                    print("Error: Invalid number format in message.")
                except Exception as e:
                    print(f"Error: {e}")

            if content == "~~~ヾ(＾∇＾)おはよー♪":
                send_message(channel_no, " ~~~ヾ(＾∇＾)おはよー♪")

            if content == "⊂二二二（　＾ω＾）二⊃ﾌﾞｰﾝ":
                send_message(channel_no, " ⊂二二二（　＾ω＾）二⊃ﾌﾞｰﾝ")

            if (
                content == "まぐろ"
                or content == "まぐ"
                or content == "マグロ"
                or content == "マグ"
                or content == "maguro"
            ):
                send_message(channel_no, "おさかな研究家のまぐろさん🐟️")

            if (
                content == "もやし"
                or content == "モヤシ"
                or content == "しょーたくん"
                or content == "まどあ"
                or content == "林しょーた"
            ):
                send_message(channel_no, "もやしはバター炒めが美味しいよね!!")

            if (
                content == "なの"
                or content == "ナノ"
                or content == "本家なの"
                or content == "本家ナノ"
                or content == "かずき"
                or content == "一輝"
                or content == "nano"
            ):
                send_message(channel_no, "Miku-Bot")

            if (
                content == "はふくん"
                or content == "はふ"
                or content == "羽風くん"
                or content == "羽風"
                or content == "hafu"
            ):
                send_message(channel_no, "⊂二二二（　＾ω＾）二⊃ﾌﾞｰﾝ")

            if (
                content == "はやしくん"
                or content == "林"
                or content == "はやし"
                or content == "林くん"
                or content == "林男"
                or content == "はやお"
            ):
                send_message(channel_no, "紫兜の相方")

            if (
                content == "ねずみ"
                or content == "nezumi"
                or content == "ネズミ"
                or content == "ねず"
                or content == "ねじゅ"
                or content == "ねずっち"
            ):
                send_message(channel_no, "ねずみは開発者兼アイドル❤")

            if content.startswith("idsearch:"):
                target_name = content[len("idsearch:") :].strip()
                response_data = get_channel_members(channel_no)
                user_list = []
                for member in response_data.get("members", []):
                    user_no = member.get("userNo")
                    name = (
                        member.get("nickName")
                        or member.get("i18nName")
                        or member.get("name")
                    )
                    if name and target_name in name:
                        user_list.append((user_no, name))
                if user_list:
                    user_messages = [
                        f"ユーザー番号: {user[0]}\nユーザー名: {user[1]}"
                        for user in user_list
                    ]
                    message = "\n".join(user_messages)
                    send_message(channel_no, message)
                else:
                    send_message(channel_no, "一致するユーザーが見つかりませんでした。")

            if content.startswith("status:"):
                date = content[len("status:") :].strip().replace("-", "")
                if len(date) == 8:
                    date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                    status_details = get_status(date)
                    if isinstance(status_details, list):
                        if status_details:
                            for detail in status_details:
                                if isinstance(detail, dict):
                                    message = (
                                        f"コンテンツ: {detail.get('コンテンツ', '不明')}\n"
                                        f"状態: {detail.get('状態', '不明')}\n"
                                        f"発生時間: {detail.get('発生時間', '不明')}\n"
                                    )
                                    send_message(channel_no, message)
                                else:
                                    send_message(channel_no, "データ形式が不正です。")
                        else:
                            send_message(
                                channel_no, "現在発生している問題はありません。"
                            )
                    else:
                        send_message(channel_no, status_details)

            if content == "resend":
                file = get_latest_image(channel_no)
                upload_file(f"./archiveimages/{file}")
                send_message(
                    channel_no,
                    f"最新のファイルです:\nhttps://nezuminff0627.pythonanywhere.com/?image={file}",
                )

            if content == "!dev:stop":
                if user_no == debugger:
                    stop(channel_no)
                else:
                    pass

            if content == "!dev:restart":
                if user_no == debugger:
                    restart(channel_no)
                else:
                    pass

            if content == "!dev:shutdown":
                if user_no == debugger:
                    shutdown(channel_no)
                else:
                    pass

            if content.startswith("exec:"):
                try:
                    command = content[len("exec:") :].strip()
                    exec(command)
                except Exception as e:
                    send_message(channel_no, f"Error: {e}")

            if content == "devcommand":
                if user_no == debugger:
                    send_message(
                        channel_no,
                        "-devcommand\n\nexec:\nshutdown()\nrestart()\nstop()",
                    )
                else:
                    pass

            if content == "leave":
                if user_no == debugger:
                    leave_group(channel_no)
                else:
                    pass

            if content.startswith("invite:"):
                try:
                    target_id = content[len("invite:") :].strip()
                    invite_user(group_id=str(channel_no), user_id=str(target_id))
                except Exception as e:
                    print(f"Error: {e}")

            if content.startswith("join:"):
                # if user_no == debugger:
                try:
                    target_id = content[len("join:") :].strip()
                    invite_user(group_id=str(target_id), user_id=str(user_no))
                except Exception as e:
                    print(f"Error: {e}")
            #     else:
            # pass

            if content.startswith("addboard:"):
                message = content[len("addboard:") :].strip()
                channel_infos = get_channel_info(channel_no)
                name = channel_infos.get("title")
                member_count = channel_infos.get("userCount")
                userInfoo = getUserInfo(user_no)
                user_name = userInfoo.get("name", {}).get("displayName", None)

                msg = add_board(
                    message, channel_no, name, member_count, user_no, user_name
                )
                send_message(channel_no, msg)

            if content == "board":
                msg = show_boards()
                send_message(channel_no, msg)

            if content.startswith("delboard:"):
                if user_no == debugger:
                    index = int(content[len("delboard:") :].strip())
                    msg = del_board(channel_no, index)
                    send_message(channel_no, msg)
                else:
                    pass

            if content.startswith("joinbord:"):
                channel_no = content[len("joinbord:") :].strip()
                user_info = getUserInfo(user_no)  # ユーザー情報を取得
                msg = join_board(channel_no, user_no, user_info)
                send_message(channel_no, msg)

            if content == "allsend":
                if user_no == debugger:
                    # notify.txtからメッセージを読み込む
                    try:
                        with open("notify.txt", "r", encoding="utf-8") as file:
                            text = file.read().strip()
                        ids = getAllGroupsId()
                        for id in ids:
                            send_message(id, text)
                    except FileNotFoundError:
                        print("エラー: notify.txtが見つかりません。")
                    except Exception as e:
                        print(f"エラー: {e}")
                else:
                    pass

            if content.startswith("memberadd:"):
                if user_no == debugger:
                    name = content[len("memberadd:") :].strip()
                    no_list = create_account(name, domainId, level_id, nheaders)
                    if no_list:
                        target = no_list[0]["userNo"]
                        send_message(
                            channel_no, f"Account Created:\nID: {target}\nName: {name}"
                        )
                        time.sleep(1)
                        invite_user(
                            group_id=str(channel_no),
                            user_id=str(target),
                            domain_id1=domainId,
                        )

                    else:
                        send_message(channel_no, "Failed to create account.")
                else:
                    pass
            if content == "alldel":
                if user_no == debugger:
                    members = get_works_member()  # メンバーを取得
                    memberlist = []  # メンバー削除情報を格納するリスト

                    print(f"取得したメンバー数: {len(members)}")  # メンバー数を表示

                    for member in members:
                        if isinstance(member, dict):
                            member_id = member.get("id")
                            name = member.get("name")

                            print(
                                f"処理中のメンバー: {name}({member_id})"
                            )  # 現在処理しているメンバーを表示

                            # userNoを除外して退会処理を呼び出す
                            if (
                                member_id != userNo
                            ):  # userNoがID1の場合は退会処理を避ける
                                member_resign(member_id)
                                del_member(member_id)
                                memberlist.append(f"{name}({member_id})")
                                print(
                                    f"削除したメンバー: {name}({member_id})"
                                )  # 削除したメンバーを表示

                    # 削除情報をまとめて送信
                    if memberlist:
                        total_removed = len(memberlist)
                        send_message(
                            channel_no,
                            "\n".join(memberlist)
                            + f"\nを削除しました\n合計削除数: {total_removed}",
                        )
                        print(f"合計削除数: {total_removed}")  # 合計削除数を表示

            if content.startswith("create:"):
                if user_no == debugger:
                    try:
                        pattern = r"create:(?P<name>.*?):(?P<targetid>\d+)"
                        match = re.match(pattern, content)
                        if match:
                            name = match.group("name")
                            targetid = match.group("targetid")
                            hostid = user_no
                            create_group(name, targetid, hostid)
                        else:
                            pass
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    pass

            if content == "gid":
                send_message(channel_no, f"{channel_no}")

            if content == "ねずわーくす":
                send_add_log(channel_no)

            if content.startswith("既読確認:"):
                target_no = int(content[len("既読確認:") :].strip())
                # print(f"ターゲット番号: {target_no}")
                data = get_read_infos(channel_no)
                # print("取得したデータ:", data)
                user_list = []
                for info in data.get("readInfos", []):
                    user_no = info.get("userNo")
                    last = info.get("readMsgs", [{}])[0].get("last")
                    if last >= message_no - target_no and user_no != userNo:
                        user_data = getUserInfo(user_no)
                        if isinstance(user_data, dict):
                            name_info = user_data.get("name", {})
                            displayName = name_info.get("displayName")
                            if displayName:
                                user_list.append(displayName)
                        else:
                            print("取得したユーザー情報は辞書型ではありません")
                # print("ユーザーリスト:", user_list)
                if user_list:
                    message = "[既読者一覧]\n" + "\n".join(user_list)
                    send_message(channel_no, message)
                else:
                    send_message(channel_no, "[既読者一覧]\n既読者がいません")

            if content == "info":
                channel_infos = get_channel_info(channel_no)
                if channel_infos is not None:
                    msg = (
                        f"Channel No: {channel_infos.get('channelNo')}\n"
                        f"Channel Type: {channel_infos.get('channelType')}\n"
                        f"User Count: {channel_infos.get('userCount')}\n"
                        f"Group Name: {channel_infos.get('title')}\n"
                        f"ICON: {channel_infos.get('photoPath')}\n"
                        f"bot Count: {channel_infos.get('unreadCount')}"
                    )
                    send_message(channel_no, msg)
                else:
                    send_message(channel_no, "チャンネル情報を取得できませんでした。")

            if content == "allgroups":
                if user_no == debugger:
                    allChats = getAllChats()
                    msg = format_join_groups(allChats)
                    send_message(channel_no, msg)
                else:
                    pass

            if content == "allfriends":
                if user_no == debugger:
                    allfriends = getAllChats()
                    msg = format_friends(allfriends)
                    send_message(channel_no, msg)
                else:
                    pass

            if content == "ais":
                image_models_message = "\n".join(image_generation_models)
                text_models_message = "\n".join(text_generation_models)
                models_message = (
                    f"画像生成モデル:\n{image_models_message}\n\n"
                    f"テキスト生成モデル:\n{text_models_message}"
                )
                send_message(channel_no, models_message)

            if content.startswith("ai:"):
                command = content[len("ai:") :].strip()
                if command.startswith("image:"):
                    parts = command[len("image:") :].strip().split(":", 1)
                    model_name = parts[0] if len(parts) > 0 else "playground-v2.5"
                    text_content = parts[1] if len(parts) > 1 else "やあ"
                    save_directory = "./output"
                    image_url = gen_ai(
                        "image", model_name, text_content, save_directory
                    )
                    send_message(channel_no, image_url)
                elif command.startswith("text:"):
                    parts = command[len("text:") :].strip().split(":", 1)
                    model_name = parts[0] if len(parts) > 0 else "gpt-4o-mini"
                    text_content = parts[1] if len(parts) > 1 else "やあ"
                    nowtime = datetime.now().strftime("%Y%m%d%H%M%S")
                    save_directory = f"./ai/output/{nowtime}"
                    text_result = gen_ai(
                        "text", model_name, text_content, save_directory
                    )
                    send_message(channel_no, text_result)
                else:
                    nowtime = datetime.now().strftime("%Y%m%d%H%M%S")
                    save_directory = f"./ai/output/{nowtime}"
                    text_result = gen_ai("text", "gpt-4o-mini", command, save_directory)
                    send_message(channel_no, text_result)

            if content.startswith("search:"):
                channel_no = channel_no
                keyword = content[len("search:") :].strip()
                response_data = search_and_fetch_messages(
                    keyword,
                    start=0,
                    display=1000,
                    channel_no=channel_no,
                )
                messages = extract_info(response_data)
                send_message(channel_no, messages)

            if content.startswith("翻訳:"):
                text_to_translate = content[len("翻訳:") :].strip()
                translated_text = translate_text(text_to_translate)
                if translated_text:
                    send_message(channel_no, translated_text)
                else:
                    send_message(
                        channel_no,
                        "翻訳ができませんでした。対応外の言語を翻訳することはできません。",
                    )

            if content.startswith("share:"):
                parts = content[len("share:") :].strip().split(":")
                if len(parts) == 2:
                    original_message_no = parts[0].strip()
                    target_channel_no = parts[1].strip()
                    shere_message(
                        original_channel_no=channel_no,
                        original_message_no=original_message_no,
                        target_channel_no=target_channel_no,
                    )

            if content.startswith("rename:"):
                if user_no == debugger:
                    name = content[len("rename:") :].strip()
                    name = name[:80]
                    half_length = len(name) // 2
                    if len(name) % 2 == 0 and half_length <= 40:
                        last_name = name[:half_length]
                        first_name = name[half_length:]
                    else:
                        last_name = name[:-1]
                        first_name = name[-1:]
                    changeProfile(
                        id=userNo,
                        level_id=level_id,
                        first_name=first_name,
                        last_name=last_name,
                        domain_id=domainId,
                        org_name="Nezumi-Project",
                        account_id=input_id,
                        private_email="greihuaop123@tatsu.uk",
                        messenger_type="TWITTER",
                        messenger_content="nezum1zum1",
                        birthday_content="20080627",
                        photo_existence=True,
                        level_name="管理職",
                        authority_level="MASTER",
                        mobile_phone_country_code="+81",
                    )
                    send_message(channel_no, "名前を変更しました")
                else:
                    pass

        except Exception as e:
            error_message = f"An unexpected error occurred: {e}\n"
            error_message += traceback.format_exc()
            print(error_message)

    # Commit changes and close the database connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    receive_messages(nheaders, domainId, userNo)

# SIMPLE-WORKS
## @ Nezumi-Project2024

## 概要
このプロジェクトは、LINE WORKSを使用してLINEユーザーとメッセージの送受信を行うためのPythonアプリケーションです。  
これは最小構成で `!test` というUSERからのメッセージに対して `Hi!!` とメッセージを送信するものです。  
必要な情報などは、ブラウザから開発者モード (F12 キー) で取得してセットしてください。

## インストール
```bash
pip install -r requirements.txt
```

## 使用方法
```bash
python example.py
```

## Next TODO

- poll処理の最適化
- 他の要素の実装と拡張
- データの見直し
- 全体の構成の見直し
- やる気を出す

---

## 未実装の実装するべき関数

| 関数名                | 動作の説明                                               | 置くべき場所               |
|---------------------|-----------------------------------------------------|------------------------|
| login               | Worksmobileサービスにログインし、セッションクッキーを返す      | works/auth.py          |
| cookies_to_header   | クッキー辞書をCookieヘッダー文字列に変換する               | works/auth.py          |
| get_status          | 指定された日付の問題の詳細を取得する                       | works/message_handler.py |
| initialize_db      | SQLiteデータベースを初期化し、メッセージテーブルを作成する     | works/database.py       |
| receive_messages     | サーバーからメッセージを受信し、処理する                   | works/message_handler.py |
| ack_message         | メッセージの受信確認を行う                               | works/message_sender.py  |
| searchSameChannel    | 指定されたユーザーIDに基づいて同じチャンネルを検索する        | works/message_handler.py |
| translate_text      | テキストを翻訳APIに送信して翻訳する                       | works/message_handler.py |
| get_channel_members  | 指定されたチャンネルのメンバーを取得する                   | works/message_handler.py |
| get_latest_image    | 指定されたチャンネルから最新の画像を取得する               | works/message_handler.py |
| search_and_fetch_messages | 指定したチャンネルからキーワードに基づいてメッセージを検索・取得する | works/message_handler.py |
| getAllChats        | すべてのチャットを取得する                               | works/message_handler.py |
| getAllFriendsId    | すべての友達のIDを取得する                               | works/message_handler.py |
| getAllGroupsId     | すべてのグループのIDを取得する                           | works/message_handler.py |
| format_friends      | 友達データを整形して表示する                             | works/message_handler.py |
| format_join_groups   | グループデータを整形して表示する                         | works/message_handler.py |
| get_read_infos      | 指定されたチャンネルの既読情報を取得する                 | works/message_handler.py |
| extract_info        | メッセージデータから情報を抽出する                       | works/message_handler.py |
| create_account      | 新しいアカウントを作成する                               | works/auth.py          |
| check_speed         | メッセージ送信の速度を測定する                           | works/message_sender.py  |
| send_message        | 指定されたグループにメッセージを送信する                 | works/message_sender.py  |
| send_sticker        | 指定されたグループにスタンプを送信する                   | works/message_sender.py  |
| getUserInfo        | 指定されたユーザーの情報を取得する                       | works/auth.py          |
| get_channel_info    | 指定されたチャンネルの情報を取得する                     | works/message_sender.py  |
| send_custom_log     | 指定されたグループにログメッセージを送信する             | works/message_sender.py  |
| shere_message       | メッセージを指定されたチャンネルに転送する               | works/message_sender.py  |
| get_works_member    | Worksメンバーを取得する                                 | works/auth.py          |
| del_member          | 指定されたユーザーを削除する                             | works/auth.py          |
| member_resign       | 指定されたユーザーを退会させる                           | works/auth.py          |

---
"""MQTT packet types.

MQTTパケットタイプの定義を提供するモジュール。

このモジュールはMQTTプロトコルで使用される各種パケットタイプを定義します。
パケットタイプは整数値で表現され、MQTT仕様に準拠しています。
"""

from enum import IntEnum, unique


@unique
class PacketType(IntEnum):
    """MQTTパケットタイプを定義する列挙型.

    MQTT v3.1.1仕様に基づくパケットタイプの列挙です。
    各パケットタイプは固有の整数値を持ち、プロトコルレベルでの識別に使用されます。

    Attributes:
        CONNECT (int): クライアントからサーバーへの接続要求パケット
        CONNACK (int): サーバーからクライアントへの接続応答パケット
        PUBLISH (int): メッセージの配信パケット
        PUBACK (int): QoS 1での PUBLISH パケットの受信確認
        SUBSCRIBE (int): トピックの購読要求パケット
        SUBACK (int): サーバーからの購読要求応答パケット
        PINGREQ (int): クライアントからのping要求パケット
        PINGRESP (int): サーバーからのping応答パケット
        DISCONNECT (int): クライアントからの正常切断要求パケット
    """

    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    SUBSCRIBE = 8
    SUBACK = 9
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14

"""MQTT packet base.

MQTTパケットの基本クラスを提供するモジュール。
"""

from typing import Optional

from .types import PacketType


def decode_remaining_length(data: bytes, start: int = 1) -> tuple[int, int]:
    """可変長の残りの長さをデコードする.

    Args:
        data (bytes): パケットデータ
        start (int, optional): デコードを開始する位置。デフォルトは1。

    Returns:
        tuple[int, int]: (残りの長さ, 次の位置)のタプル

    Raises:
        ValueError: 不正なデータ形式の場合
    """
    multiplier = 1
    value = 0
    index = start

    while True:
        if index >= len(data):
            raise ValueError("パケットが不完全です")

        byte = data[index]
        value += (byte & 0x7F) * multiplier
        multiplier *= 128
        index += 1

        if multiplier > 128**3:
            raise ValueError("不正な長さ形式です")

        if not byte & 0x80:
            break

    return value, index


class MQTTPacket:
    """MQTTパケットを表すクラス."""

    def __init__(
        self,
        packet_type: PacketType,
        flags: int,
        remaining_length: int,
        payload: Optional[bytes] = None,
        raw_packet: Optional[bytes] = None,
    ) -> None:
        """MQTTパケットを初期化します.

        Args:
            packet_type: パケットタイプ
            flags: フラグ
            remaining_length: 残りの長さ
            payload: ペイロード
            raw_packet: 生のパケットデータ
        """
        self.packet_type = packet_type
        self.flags = flags
        self.remaining_length = remaining_length
        self.payload = payload
        self._raw_packet = raw_packet

    @property
    def packet(self) -> bytes:
        """パケットのバイナリデータを取得します."""
        if self._raw_packet is not None:
            return self._raw_packet
        # 生のパケットデータがない場合は、ヘッダーとペイロードを結合
        if self.payload is None:
            return self.header
        return self.header + self.payload

    @property
    def header(self) -> bytes:
        """パケットヘッダーを生成する.

        Returns:
            bytes: パケットヘッダーのバイト列
        """
        first_byte = (self.packet_type.value << 4) | self.flags
        remaining_bytes = self._encode_remaining_length()
        return bytes([first_byte] + remaining_bytes)

    def _encode_remaining_length(self) -> list[int]:
        """残りの長さを可変長エンコードする.

        Returns:
            list[int]: エンコードされた長さのバイトリスト
        """
        remaining_bytes = []
        length = self.remaining_length

        while True:
            byte = length % 128
            length = length // 128
            if length > 0:
                byte |= 0x80
            remaining_bytes.append(byte)
            if length == 0:
                break

        return remaining_bytes

    def get_message_id(self) -> Optional[int]:
        """メッセージIDを取得する.

        Returns:
            Optional[int]: メッセージID。存在しない場合はNone。
        """
        if self.payload is None or len(self.payload) < 2:
            return None
        return int.from_bytes(self.payload[:2], byteorder="big")

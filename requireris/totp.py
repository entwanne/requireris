from base64 import b32decode
from time import time as current_time_unix
import hmac
from hashlib import sha1
import struct


def ull_to_bytes(i: int) -> bytes:
    "Makes an 8-bytes string from an unsigned long long (big-endian)"
    return struct.pack('>Q', i)


def bytes_to_ui(data: bytes) -> int:
    "Makes an unsigned int from a 4-bytes string (big-endian)"
    result, = struct.unpack('>I', data)
    return result


def hmac_sha1(key: bytes, time: int) -> bytes:
    return hmac.new(key, ull_to_bytes(time), sha1).digest()


def last_nibble(data: bytes) -> int:
    return data[-1] & 0xF


def remove_first_bit(data: bytes) -> bytes:
    return bytes([data[0] & 0x7F, *data[1:]])


def padding_6(i: int) -> str:
    return f'{i:06}'


def generate_totp(secret: str | bytes) -> str:
    key = b32decode(secret)
    data = hmac_sha1(key, int(current_time_unix() / 30))
    offset = last_nibble(data)
    truncated_data = data[offset:offset+4]
    truncated_data = remove_first_bit(truncated_data)
    code = bytes_to_ui(truncated_data) % 1000000
    return padding_6(code)

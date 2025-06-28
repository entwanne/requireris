import time
from base64 import b32decode
import hmac
from hashlib import sha1
import struct


def ull_to_bytes(i: int) -> bytes:
    "Makes an 8-bytes string from an unsigned long long (big-endian)"
    try:
        return struct.pack('>Q', i)
    except struct.error as e:
        raise ValueError(i) from e


def bytes_to_ui(data: bytes) -> int:
    "Makes an unsigned int from a 4-bytes string (big-endian)"
    try:
        result, = struct.unpack('>I', data)
    except struct.error as e:
        raise ValueError(data) from e
    return result


def hmac_sha1(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, sha1).digest()


def last_nibble(data: bytes) -> int:
    if not data:
        return 0
    return data[-1] & 0xF


def remove_first_bit(data: bytes) -> bytes:
    if not data:
        return b''
    return bytes([data[0] & 0x7F, *data[1:]])


def padding_6(i: int) -> str:
    if not 0 <= i < 10**6:
        raise ValueError(i)
    return f'{i:06}'


def get_time():
    return int(time.time() / 30)


def generate_totp(secret: str | bytes) -> str:
    key = b32decode(secret.upper())
    data = hmac_sha1(key, ull_to_bytes(get_time()))
    offset = last_nibble(data)
    truncated_data = data[offset:offset+4]
    truncated_data = remove_first_bit(truncated_data)
    code = bytes_to_ui(truncated_data) % 1000000
    return padding_6(code)

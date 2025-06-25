from base64 import b32decode as base32decode
from time import time as current_time_unix
import hmac
from hashlib import sha1
import struct


# Makes an 8-bytes string from an unsigned long long (big-endian)
def ull_to_str(l):
    return struct.pack('>Q', int(l))


# Makes an unsigned int from a 4-bytes string (big-endian)
def str_to_ui(s):
    return struct.unpack('>I', s)[0]


def hmac_sha1(key, message):
    return hmac.new(key, ull_to_str(message), sha1).digest()


def last_nibble(hash):
    return hash[-1] & 15


def remove_first_bit(hash):
    return bytes([hash[0] & 0x7f]) + hash[1:]


def padding_6(i):
    return '%06d' % i


def auth(secret):
    key = base32decode(secret)
    message = current_time_unix() // 30
    hash = hmac_sha1(key, message)
    offset = last_nibble(hash)
    truncated_hash = hash[offset:offset+4]
    truncated_hash = remove_first_bit(truncated_hash)
    code = str_to_ui(truncated_hash) % 1000000
    return padding_6(code)

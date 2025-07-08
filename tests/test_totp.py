import pytest

from requireris.totp import ull_to_bytes, bytes_to_ui, hmac_sha1, last_nibble, remove_first_bit, padding_6, get_time, generate_totp


@pytest.mark.parametrize(
    'value,expected',
    [
        (0, b'\x00' * 8),
        (0x12, b'\x00' * 7 + b'\x12'),
        (0x1234, b'\x00' * 6 + b'\x12\x34'),
        (0x1234567890ABCDEF, b'\x12\x34\x56\x78\x90\xAB\xCD\xEF'),
        (0xFFFFFFFFFFFFFFFF, b'\xFF' * 8),
    ],
)
def test_ull_to_bytes(value, expected):
    assert ull_to_bytes(value) == expected


@pytest.mark.parametrize(
    'value',
    [
        -1,
        0x10000000000000000,
    ],
)
def test_ull_to_bytes_errors(value):
    with pytest.raises(ValueError):
        ull_to_bytes(value)


@pytest.mark.parametrize(
    'data,expected',
    [
        (b'\x00' * 4, 0),
        (b'\x12\x34\x56\x78', 0x12345678),
        (b'\xFF' * 4, 0xFFFFFFFF),
    ],
)
def test_bytes_to_ui(data, expected):
    assert bytes_to_ui(data) == expected


@pytest.mark.parametrize(
    'data',
    [
        b'',
        b'\x12\x34\x56',
        b'\x12\x34\x56\x78\x90',
    ],
)
def test_bytes_to_ui_errors(data):
    with pytest.raises(ValueError):
        bytes_to_ui(data)


@pytest.mark.parametrize(
    'key,time,expected',
    [
        (b'', b'', b'\xFB\xDB\x1D\x1B\x18\xAA\x6C\x08\x32\x4B\x7D\x64\xB7\x1F\xB7\x63\x70\x69\x0E\x1D'),
        (b'key', b'message', b'\x20\x88\xDF\x74\xD5\xF2\x14\x6B\x48\x14\x6C\xAF\x49\x65\x37\x7E\x9D\x0B\xE3\xA4'),
        (b'key', b'other', b'\xE3\xBF\xA7\x3B\xB6\xBB\x28\x43\xC6\x35\x32\x25\xEC\x59\x6D\xE5\x71\xE9\xD2\xDD'),
        (b'other', b'message', b'\x4F\x6B\xEE\xEA\x84\x0D\x3B\xAB\xFC\x05\x74\x64\x14\x64\x33\xFD\x79\xCB\x4F\x79'),
        (b'other', b'other', b'\xB0\x5D\x36\xE0\x9D\x15\x8C\xC7\x13\x47\xCE\xBE\xF1\x9E\xD5\x5B\x64\x58\x18\xCD'),
    ],
)
def test_hmac_sha1(key, time, expected):
    assert hmac_sha1(key, time) == expected


@pytest.mark.parametrize(
    'data,expected',
    [
        (b'', 0),
        (b'\x00', 0),
        (b'\xFF', 0xF),
        (b'\xA3', 3),
        (b'\x12\x34\x56', 6),
    ],
)
def test_last_nibble(data, expected):
    assert last_nibble(data) == expected


@pytest.mark.parametrize(
    'data,expected',
    [
        (b'', b''),
        (b'\x00', b'\x00'),
        (b'\xFF', b'\x7F'),
        (b'\xA3', b'\x23'),
        (b'\x12\x34\x56', b'\x12\x34\x56'),
        (b'\x89\xAB\xCD', b'\x09\xAB\xCD'),
    ],
)
def test_remove_first_bit(data, expected):
    assert remove_first_bit(data) == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        (0, '000000'),
        (123, '000123'),
        (123456, '123456'),
        (999999, '999999'),
    ],
)
def test_padding_6(value, expected):
    assert padding_6(value) == expected


@pytest.mark.parametrize(
    'value',
    [
        -1,
        1000000,
    ],
)
def test_padding_6_errors(value):
    with pytest.raises(ValueError):
        padding_6(value)


@pytest.mark.parametrize(
    'current_time,expected',
    [
        (0.0, 0),
        (29.9999, 0),
        (30.0, 1),
        (123456.789, 4115),
    ],
)
def test_get_time(mocker, current_time, expected):
    mocker.patch('time.time', return_value=current_time)
    assert get_time() == expected


@pytest.mark.parametrize(
    'secret,current_time,expected',
    [
        ('', 0.0, '328482'),
        ('', 123456.789, '291914'),
        ('AAAAAAAAAAAAAAAA', 123456.789, '291914'),
        ('ABCDEFGHIJKLMNOP', 123456.789, '258941'),
        (b'ABCDEFGHIJKLMNOP', 123450.0, '258941'),
        ('ABCDEFGHIJKLMNOP', 9876543.21, '197309'),
        ('abcdefghijklmnop', 9876543.0, '197309'),
    ],
)
def test_generate_totp(mocker, secret, current_time, expected):
    mocker.patch('time.time', return_value=current_time)
    assert generate_totp(secret) == expected

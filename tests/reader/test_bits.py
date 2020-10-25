from io import BytesIO
from duckparse.reader import Reader


def test_read_bits_le_startw8multi():
    data = Reader(
        BytesIO(
            b"\xf7\x30\x8a\x1e\xce\xf2\xde\xe9\x12\x5f\xd7\x7c\x2e\x7f\x63\x19\xf2\x62\x83\x20\x72\x40\x35\x99"
        ),
    )

    results = (
        (15, 0x30F7, 1, 7),
        (19, 0x43D14, 4, 2),
        (26, 0x277BCB3, 7, 4),
        (11, 0x12E, 8, 7),
        (5, 0x1E, 9, 4),
        (18, 0x3CD75, 11, 6),
        (2, 0x01, 12, 0),
        (14, 0x3F2E, 13, 6),
        (21, 0x8658D, 16, 3),
        (24, 0x106C5E, 19, 3),
        (7, 0x44, 20, 2),
        (7, 0x1C, 21, 1),
        (3, 0x00, 21, 4),
        (3, 0x04, 21, 7),
        (3, 0x02, 22, 2),
        (3, 0x05, 22, 5),
        (3, 0x01, 23, 0),
    )

    byte_needle = bit_needle = 0
    for bit_count, result, byte_needle, bit_needle in results:
        assert data.read_bits_int_le(bit_count) == result
        assert bit_needle == data._Reader__bit_needle
        assert byte_needle == data._Reader__current_byte


def test_read_bits_le_startw8half():
    data = Reader(BytesIO(b"\xf7\x30\x8a"),)

    results = (
        (3, 0x07, 0, 3),
        (3, 0x06, 0, 6),
        (3, 0x03, 1, 1),
        (3, 0x00, 1, 4),
    )

    byte_needle = bit_needle = 0
    for bit_count, result, byte_needle, bit_needle in results:
        assert data.read_bits_int_le(bit_count) == result
        assert bit_needle == data._Reader__bit_needle
        assert byte_needle == data._Reader__current_byte


def test_read_bits_le_startw8single():
    data = Reader(BytesIO(b"\xf7\x30\x8a\x1e"),)

    results = (
        (8, 0xF7, 1, 0),
        (3, 0x00, 1, 3),
        (3, 0x06, 1, 6),
        (3, 0x00, 2, 1),
    )

    byte_needle = bit_needle = 0
    for bit_count, result, byte_needle, bit_needle in results:
        assert data.read_bits_int_le(bit_count) == result
        assert bit_needle == data._Reader__bit_needle
        assert byte_needle == data._Reader__current_byte

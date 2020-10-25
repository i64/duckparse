from io import BytesIO
from duckparse.reader import Reader


def test_read_byte():
    data = Reader(BytesIO(b"\xf7\x30\x8a"),)

    assert b"\xf7" == data.read_bytes(1)
    assert b"\x30\x8a" == data.read_bytes(2)

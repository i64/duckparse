from io import BytesIO
from duckparse.reader import Reader


def test_read_hybrid():
    data = Reader(BytesIO(b"\xf7\x30\x8a\xea"),)

    assert b"\xf7" == data.read_bytes(1)
    assert 8 == data._Reader__bit_needle
    assert 0 == data._Reader__current_byte

    assert 0b110000 == data.read_bits_int_le(6)
    assert 6 == data._Reader__bit_needle
    assert 1 == data._Reader__current_byte

    assert 0b00 == data.read_bits_int_le(2)
    assert 0 == data._Reader__bit_needle
    assert 2 == data._Reader__current_byte

    assert 0b10 == data.read_bits_int_le(2)
    assert 2 == data._Reader__bit_needle
    assert 2 == data._Reader__current_byte

    assert b"\xea" == data.read_bytes(1)
    assert 8 == data._Reader__bit_needle
    assert 3 == data._Reader__current_byte

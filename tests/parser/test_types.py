from io import BytesIO

from duckparse import stream
from duckparse.btypes import U8, U16, U32, U64, Bits


@stream
class TestClass:
    uu8: U8
    bb2: Bits[2]
    uu16: U16
    uu32: U32
    bb1: Bits[1]
    uu64: U64


def test_unsigned():
    DATA = TestClass(
        BytesIO(
            b"\xf7\x30\x8a\x1e\xce\xf2\xde\xe9\x12\x5f\xd7\x7c\x2e\x7f\x63\x19\xf2"
        )
    )
    assert DATA.uu8 == 0xF7
    assert DATA.bb2 == 0x00
    assert DATA.uu16 == 0x1E8A
    assert DATA.uu32 == 0xE9DEF2CE
    assert DATA.bb1 == 0x00
    assert DATA.uu64 == 0xF219637F2E7CD75F

# from . import c_types
from .kindprotocol import datakind
from .reader import Reader

from typing import Any, Tuple, Union, Dict, List, Callable, Optional

from .exceptions import ValidationError


@datakind
class Byte:
    def __processor__(
        self, reader: Reader, params: Tuple[int]
    ) -> bytearray:
        (size,) = params
        return reader.read_bytes(size)


@datakind
class Bits:
    def __processor__(
        self, reader: Reader, params: Tuple[int]
    ) -> bytearray:
        (size,) = params
        return reader.read_bits_int_le(size)


@datakind
class U8:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.u8.unpack(reader.read_bytes(1))[0]


@datakind
class I8:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.i8.unpack(reader.read_bytes(1))[0]


@datakind
class U16:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.u16.unpack(reader.read_bytes(2))[0]


@datakind
class I16:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.i16.unpack(reader.read_bytes(2))[0]


@datakind
class U32:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.u32.unpack(reader.read_bytes(4))[0]


@datakind
class I32:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.i32.unpack(reader.read_bytes(4))[0]


@datakind
class U64:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.u64.unpack(reader.read_bytes(8))[0]


@datakind
class I64:
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.i64.unpack(reader.read_bytes(8))[0]


@datakind
class String:
    def read_to_zero(self, reader: Reader, params: Tuple) -> bytearray:
        data = bytearray()
        while (byte := reader.read_bytes(1)) != b"\x00":
            data += byte
        return data

    def __processor__(
        self, reader: Reader, params: Tuple[int, str]
    ) -> str:
        size, _encoding = params
        encoding = _encoding or "ascii"
        if size == -1:
            data = self.read_to_zero(reader)
        else:
            data = reader.read_bytes(size)
        return data.decode(encoding)


@datakind
class Array:
    def __processor__(self, reader: Reader, params: Tuple[int]) -> str:
        (size,) = params
        return list(reader.read_bytes(size))


@datakind
class Contents:
    def __processor__(self, reader: Reader, params: Tuple[bytes]) -> str:
        (expected,) = params
        found = reader.read_bytes(len(expected))

        if expected != found:
            raise ValidationError(expected, found)

        return expected

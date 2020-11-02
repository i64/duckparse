import struct
from collections import namedtuple

_Ctypes = namedtuple(
    "_Ctypes",
    ["i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "f32", "f64"],
)

i8 = struct.Struct("b")
u8 = struct.Struct("B")

i16_be = struct.Struct(">h")
i32_be = struct.Struct(">i")
i64_be = struct.Struct(">q")

u16_be = struct.Struct(">H")
u32_be = struct.Struct(">I")
u64_be = struct.Struct(">Q")


u16_le = struct.Struct("<H")
u32_le = struct.Struct("<I")
u64_le = struct.Struct("<Q")

i16_le = struct.Struct("<h")
i32_le = struct.Struct("<i")
i64_le = struct.Struct("<q")

f32_be = struct.Struct(">f")
f64_be = struct.Struct(">d")

f32_le = struct.Struct("<f")
f64_le = struct.Struct("<d")


BigEndian = _Ctypes(
    i8, i16_be, i32_be, i64_be, u8, u16_be, u32_be, u64_be, f32_be, f64_be
)

LittleEndian = _Ctypes(
    i8, i16_le, i32_le, i64_le, u8, u16_le, u32_le, u64_le, f32_le, f64_le
)

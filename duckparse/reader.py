import sys
from os import SEEK_END, SEEK_SET

from .c_types import BigEndian, LittleEndian, _Ctypes

from dataclasses import dataclass

from typing import (
    BinaryIO,
    Optional,
    Tuple,
)


@dataclass
class Reader:
    io: BinaryIO

    size: int = 0
    endianness: str = sys.byteorder
    primitive: _Ctypes = LittleEndian
    # we have to save the last byte for bit operations
    __last_byte: int = 0
    # its our bit counter
    __bit_needle: int = 8
    # and this is our inverse bit counter
    __remaining_bits: int = 0

    if __debug__:
        __current_byte: int = -1

    def __post_init__(self):
        self.__set_size()
        if self.endianness == "big":
            self.primitive = BigEndian

    def __set_size(self):
        cur = self.io.tell()
        self.io.seek(0, SEEK_END)
        self.size = self.io.tell()
        self.io.seek(cur, SEEK_SET)

    def read_bytes(
        self,
        size: int,
        input_term: Optional[bytearray] = None,
        allign: bool = True,
    ) -> bytearray:
        if size:
            content = bytearray(self.io.read(size))
            self.__last_byte = content[-1]
            if allign:
                self.__bit_needle = 8
                self.__remaining_bits = 0
            if __debug__:
                self.__current_byte += size
        else:
            content = bytearray()
        return content

    def read_bits_int_le(self, size) -> int:
        if (non_exist_bits := size - self.__remaining_bits) >= 0:
            # 1 bit  => 1 byte,  1 bit
            # 8 bits => 1 byte,  0 bit
            # 9 bits => 2 bytes, 1 bit
            byte_len, bit_len = divmod(non_exist_bits, 8)
            # align the bit needle and clear the counter
            allign, bits_left = self.__clearread_bits()
            # read as byte_len and convert it to int
            bit_chunk = int.from_bytes(
                self.read_bytes(byte_len + 1), self.endianness,
            )
            # combine bit_chunk and allign
            byte_chunk = (bit_chunk << bits_left) | allign
        else:
            bit_len = size
            # read first n bits
            byte_chunk = self.__last_byte >> self.__bit_needle

        self.__bit_needle = (self.__bit_needle + bit_len) % 8
        # make a mask for first "size" bits
        # for size = 5 -> mask = 0b11111
        mask = (1 << size) - 1
        self.__remaining_bits = 8 - self.__bit_needle
        return byte_chunk & mask

    def __clearread_bits(self) -> Tuple[int, int]:
        trim = self.__bit_needle
        # read rest of the bits from the last byte
        allign = self.__last_byte >> trim
        # reset the bit counter
        self.__bit_needle = 0
        return allign, 8 - trim

import pathlib

from duckparse.btypes import (
    Var,
    U16,
    U32,
    I32,
    Contents,
    Byte,
    String,
    RepeatN,
    RepeatEOS,
)

from duckparse.reader import Reader
from duckparse import stream, section, datakind, enumkind

from typing import Tuple, Union


@enumkind
class Compression:
    NONE = 0
    SHRUNK = 1
    REDUCED_1 = 2
    REDUCED_2 = 3
    REDUCED_3 = 4
    REDUCED_4 = 5
    IMPLODED = 6
    DEFLATED = 8
    ENHANCED_DEFLATED = 9
    PKWARE_DCL_IMPLODED = 10
    BZIP2 = 12
    LZMA = 14
    IBM_TERSE = 18
    IBM_LZ77_Z = 19
    PPMD = 98


@section
class DataDescriptor:
    crc32: U32
    len_body_compressed: U32
    len_body_uncompressed: U32


@section
class CentralDirEntry:
    version_made_by: U16
    version_needed_to_extract: U16
    flags: U16
    compression_method: Compression[U16]
    last_mod_file_time: U16
    last_mod_file_date: U16
    crc32: U32
    len_body_compressed: U32
    len_body_uncompressed: U32
    len_file_name: U16
    len_extra: U16
    len_comment: U16
    disk_number_start: U16
    int_file_attr: U16
    ext_file_attr: U32
    ofs_local_header: I32
    file_name: String[Var("len_file_name"), "utf-8"]


@section
class LocalFileHeader:
    version: U16
    flags: U16
    compression_method: Compression[U16]
    file_mod_time: U16
    file_mod_date: U16
    crc32: U32
    len_body_compressed: U32
    len_body_uncompressed: U32
    len_file_name: U16
    len_extra: U16
    file_name: String[Var("len_file_name"), "utf-8"]


@section
class LocalFile:
    header: LocalFileHeader
    body: Byte[Var("header.len_body_compressed")]


@section
class EndOfCentralDir:
    disk_of_end_of_central_dir: U16
    disk_of_central_dir: U16
    num_central_dir_entries_on_disk: U16
    num_central_dir_entries_total: U16
    len_central_dir: U32
    ofs_central_dir: U32
    len_comment: U16
    comment: String[Var("len_comment"), "utf-8"]


@datakind
class SectionBody:
    def __processor__(
        self, reader: Reader, params: Tuple[int]
    ) -> Union[
        CentralDirEntry, LocalFile, EndOfCentralDir, DataDescriptor
    ]:
        (section_type,) = params
        if section_type == 0x0201:
            return CentralDirEntry(reader)
        elif section_type == 0x0403:
            return LocalFile(reader)
        elif section_type == 0x0605:
            return EndOfCentralDir(reader)
        elif section_type == 0x0807:
            return DataDescriptor(reader)


@section
class PkSection:
    magic: Contents[b"PK"]
    section_type: U16
    body: SectionBody[Var("section_type")]


@stream
class Zip:
    sections: RepeatEOS[PkSection]


if __name__ == "__main__":
    with open(
        f"{pathlib.Path(__file__).parent.absolute()}/sample1.zip", "rb"
    ) as zip_io:
        print(Zip(zip_io))

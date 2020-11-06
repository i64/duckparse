import pathlib

from os import SEEK_END

from duckparse.btypes import U8, U16, U32, Contents
from duckparse import stream, section, datakind, enumkind

from duckparse.reader import Reader


@enumkind
class ColorMapEnum:
    NO_COLOR_MAP = 0
    HAS_COLOR_MAP = 1


@enumkind
class ImageTypeEnum:
    NO_IMAGE_DATA = 0
    UNCOMP_COLOR_MAPPED = 1
    UNCOMP_TRUE_COLOR = 2
    UNCOMP_BW = 3
    RLE_COLOR_MAPPED = 9
    RLE_TRUE_COLOR = 10
    RLE_BW = 11


@datakind
class ImageId(U8):
    __reprocess_after__ = "img_descriptor"
    __reprocessor_name__ = "image_id"

    def __reprocessor__(self, reader: Reader, params):
        image_id_len = params[0].image_id_len
        return list(reader.read_bytes(image_id_len))


@datakind
class VersionMagic(Contents):
    __reprocess_after__ = "version_magic"
    __reprocessor_name__ = "is_valid"

    def __reprocessor__(self, reader: Reader, params):
        version_magic = params[0].version_magic
        return version_magic is not None


@section
class Footer:
    ext_area_ofs: U32
    dev_dir_ofs: U32
    version_magic: VersionMagic[
        b"\x54\x52\x55\x45\x56\x49\x53\x49\x4f\x4e\x2d\x58\x46\x49\x4c\x45\x2e\x00"
    ]

    def __duckparse_first__(self, reader: Reader):
        reader.io.seek(-26, SEEK_END)


@stream
class TGA:
    """
    TGA (AKA Truevision TGA, AKA TARGA), is a raster image file format
    created by Truevision. It supports up to 32 bits per pixel (three
    8-bit RGB channels + 8-bit alpha channel), color mapping an
    """

    image_id_len: ImageId
    color_map_type: ColorMapEnum[U8]
    image_type: ImageTypeEnum[U8]
    color_map_ofs: U16
    num_color_map: U16
    color_map_depth: U8
    x_offset: U16
    y_offset: U16
    width: U16
    height: U16
    image_depth: U8
    img_descriptor: U8
    footer: Footer


if __name__ == "__main__":
    with open(
        f"{pathlib.Path(__file__).parent.absolute()}/earth.tga", "rb"
    ) as tga_sample:
        print(TGA(tga_sample))

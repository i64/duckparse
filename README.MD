# duckparse [WIP]

Duckparse is binary parsers for humans. 
It is similar to [Construct](https://construct.readthedocs.io/en/latest/) and [Kaitai](https://kaitai.io/). But it's more easy to write. 

Duckparse is using [PEP 526](https://www.python.org/dev/peps/pep-0526/) type annotations. Check our [gallery](https://github.com/CyberSaxosTiGER/duckparse/blob/master/gallery/) for more examples!

Example:

```python

>>> from io import BytesIO

>>> from duckparse import stream_parser
>>> from duckparse.btypes import U8, Bits

>>> @stream_parser
... class ExampleFormat:
...     width: U8
...     height: U8
...     some_bitfield: Bits[1]
 
>>> result = ExampleFormat(BytesIO(b"\x03\x02\xFF"))
>>> print(result)
ExampleFormat(width=3, height=2, some_bitfield=1)
```

Or you can define a new data type or an enum

```python
from duckparse import datakind, enumkind

@datakind
class I64():
    def __processor__(self, reader: Reader) -> bytearray:
        return reader.primitive.i64.unpack(reader.read_bytes(8))[0]

@enumkind
class Color:
    RED = 1
    GREEN = 2
    BLUE = 3

```


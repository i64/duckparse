from enum import Enum
from dataclasses import dataclass

from .utils import generic_repeat, whilor

from .reader import Reader
from .kindprotocol import Kind, KindProtocol, datakind
from .consts import PROCESSOR_FUNCTION_FIELD

from typing import Iterable, Tuple


@dataclass
class VarKind:
    var_name: str
    __duckparse_kindguard__: bool = True

    def __repr__(self):
        return f"self.{self.var_name}"


def __enum__preprocessor__(
    self, reader: Reader, params: Tuple[int]
) -> Enum:
    (idx,) = params
    return self.__masked_enum__(idx)


def enumkind(cls):
    def wrap(cls):
        cls.__masked_enum__ = Enum(cls.__name__, cls.__dict__)
        cls.__masked_enum__.__repr__ = cls.__masked_enum__.__str__
        setattr(cls, PROCESSOR_FUNCTION_FIELD, __enum__preprocessor__)
        return datakind(cls)

    if cls is None:
        return wrap

    return wrap(cls)


class RepeatKind(Kind):
    ...


class RepeatN(RepeatKind):
    def __class_getitem__(cls, params):
        assert isinstance(params, tuple)
        assert len(params) == 2
        body, condition = params
        new_params = body, f"range({condition})"
        return cls(instance=None, params=new_params)


class RepeatEOS(RepeatKind):
    def __class_getitem__(cls, body):
        new_params = (
            body,
            f"whilor(lambda: self.reader.io.tell() != self.reader.size)",
        )
        return cls(
            instance=None,
            params=new_params,
            kind_locals={"whilor": whilor},
        )

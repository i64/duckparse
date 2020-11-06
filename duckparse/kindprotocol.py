from .reader import Reader

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, Any

from .consts import DATAKIND_GUARD_NAME, PROCESSOR_NAME


@dataclass
class Kind:
    instance: Any
    params: Optional[Tuple]


def _datakind__getitem__(cls, params):
    if not isinstance(params, tuple):
        params = (params,)
    return Kind(instance=cls(), params=params)


def datakind(cls):
    def wrap(cls):
        cls.__class_getitem__ = classmethod(_datakind__getitem__)
        setattr(cls, DATAKIND_GUARD_NAME, True)
        return cls

    if cls is None:
        return wrap

    return wrap(cls)


def __enum__preprocessor__(
    self, reader: Reader, params: Tuple[int]
) -> Enum:
    (idx,) = params
    return self.__masked_enum__(idx)


def enumkind(cls):
    def wrap(cls):
        cls.__masked_enum__ = Enum(cls.__name__, cls.__dict__)
        setattr(cls, PROCESSOR_NAME, __enum__preprocessor__)
        return datakind(cls)

    if cls is None:
        return wrap

    return wrap(cls)

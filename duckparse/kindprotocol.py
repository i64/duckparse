from .reader import Reader

from dataclasses import dataclass
from typing import Optional, Tuple, Any, Dict

from .consts import DATAKIND_GUARD_FIELD


class KindProtocol:
    __duckparse_kindguard__: bool


@dataclass
class Kind:
    instance: KindProtocol
    params: Optional[Tuple]
    kind_locals: Optional[Dict[str, Any]] = None


def _datakind__getitem__(cls, params):
    if not isinstance(params, tuple):
        params = (params,)
    return Kind(instance=cls(), params=params)


def datakind(cls):
    def wrap(cls):
        cls.__class_getitem__ = classmethod(_datakind__getitem__)
        setattr(cls, DATAKIND_GUARD_FIELD, True)
        return cls

    if cls is None:
        return wrap

    return wrap(cls)

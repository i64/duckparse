from abc import ABCMeta
from .reader import Reader

from typing import Optional, Tuple, Any


def __getitem__(cls, params):
    if not isinstance(params, tuple):
        params = (params,)
    return (cls(), params)


def datakind(cls):
    def wrap(cls):
        cls.__class_getitem__ = classmethod(__getitem__)
        return cls

    if cls is None:
        return wrap

    return wrap(cls)

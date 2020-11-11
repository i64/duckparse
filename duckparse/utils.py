from contextlib import suppress
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")


def whilor(condution: Callable[[], bool]) -> Iterable[bool]:
    while condution():
        yield True


def generic_repeat(body: Callable[[], T], condution: Iterable) -> List[T]:
    return [body() for _ in condution]


def resolve(elem) -> str:
    with suppress(AttributeError):
        return elem.__name__
    return elem.__class__.__name__

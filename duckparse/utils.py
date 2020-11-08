from contextlib import suppress
from typing import Callable, Iterable, List


def whilor(condution: Callable[[], bool]):
    while condution():
        yield True
    return False


def generic_repeat(body: Callable, condution: Iterable):
    return [body() for _ in condution]


def resolve(elem):
    with suppress(AttributeError):
        return elem.__name__
    return elem.__class__.__name__

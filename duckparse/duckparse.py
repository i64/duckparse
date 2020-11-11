from enum import Enum

from .utils import resolve

from .reader import Reader
from .kindprotocol import Call, Assignment

from .consts import (
    READER_NAME,
    STREAM_TYPE_FIELD,
    PREFUNCTION_FIELD,
)

from typing import (
    Any,
    Tuple,
    Union,
    Dict,
    List,
    Iterable,
    Callable,
    Optional,
    TypeVar,
)

__all__ = ["stream", "section"]

T = TypeVar("T")


class StreamType(Enum):
    STREAM = 0
    SECTION = 1


def _ss_into_call(
    cls,
    cls_locals: Dict[str, Any],
    par_counter: Optional[List[int]] = None,
    reprocessors_dict: Optional[Dict[str, List[Assignment]]] = None,
) -> Call:
    par_counter = par_counter or [0]
    if (
        hasattr(cls, STREAM_TYPE_FIELD)
        and getattr(cls, STREAM_TYPE_FIELD) is StreamType.SECTION
    ):
        function_name = f"__duckparse_function_{resolve(cls)}__"
        cls_locals[function_name] = cls
        return Call(function_name=function_name,)
    raise ValueError


def _create_fn(
    name: str,
    _args: Iterable[str],
    _body: Iterable[str],
    *,
    globals: Dict[str, Any] = None,
    locals: Dict[str, Any] = None,
) -> Callable:
    # SOURCE: https://github.com/python/cpython/blob/master/Lib/dataclasses.py
    # Note that we mutate locals when exec() is called.  Caller
    # beware!  The only callers are internal to this module, so no
    # worries about external callers.
    locals = locals or {}
    globals = globals or {}

    args = ",".join(_args)
    body = "\n".join(f"  {b}" for b in _body)

    # Compute the text of the entire function.
    txt = f" def {name}({args}):\n{body}"
    # print(txt)

    local_vars = ", ".join(locals.keys())
    txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"
    ns: Dict[str, Callable] = {}
    exec(txt, globals, ns)
    func = ns["__create_fn__"](**locals)
    for arg, annotation in func.__annotations__.copy().items():
        func.__annotations__[arg] = locals[annotation]
    return func


def _make_repr(
    cls_name: str,
    assigments: List[Assignment],
    cls_locals: Dict[str, Any],
) -> Callable:
    arguments = ", ".join(
        f"{assigment.assing_to}={{self.{assigment.assing_to}!r}}"
        for assigment in assigments
        if hasattr(assigment, "assing_to")
        and assigment.assing_to is not None
    )
    function_body = [f"return f'{cls_name}({arguments})'"]
    function = _create_fn(
        "__repr__", ("self",), function_body, locals=cls_locals
    )

    return function


def _make_init(
    assigments: List[Assignment],
    cls_locals: Dict[str, Any],
    is_section: bool = False,
) -> Callable:
    if is_section:
        function_body = (
            f"{READER_NAME} = reader",
            *(repr(assigment) for assigment in assigments),
        )
        function = _create_fn(
            "__init__",
            ("self", "reader"),
            function_body,
            locals=cls_locals,
        )
    else:
        cls_locals["Reader"] = Reader
        function_body = (
            f"{READER_NAME} = Reader(io)",
            *(repr(assigment) for assigment in assigments),
        )
        function = _create_fn(
            "__init__", ("self", "io"), function_body, locals=cls_locals
        )

    return function


def _process_class(cls: T, is_section: bool = False) -> T:
    if hasattr(cls, "__annotations__"):
        cls_annotations = cls.__annotations__
        del cls.__annotations__
    else:
        # TODO: Raise an error
        ...
    cls_locals: Dict[str, Any] = dict()

    init_body: List[Assignment] = list()
    reprocessors_dict: Dict[str, List[Assignment]] = dict()

    if hasattr(cls, PREFUNCTION_FIELD):
        prefunction = getattr(cls, PREFUNCTION_FIELD)
        cls_locals[resolve(prefunction)] = prefunction
        init_body.append(
            Assignment(
                value=Call(function_name=f"self.{resolve(prefunction)}",)
            )
        )

    for field_name, kind in zip(
        cls_annotations.keys(), cls_annotations.values(),
    ):
        call = kind.into_call(
            cls_locals=cls_locals, reprocessors_dict=reprocessors_dict
        )
        init_body.append(Assignment(assing_to=field_name, value=call))

        if reprocessor := reprocessors_dict.get(field_name):
            init_body.extend(reprocessor)

    setattr(
        cls, "__init__", _make_init(init_body, cls_locals, is_section)
    )
    setattr(
        cls, "__repr__", _make_repr(resolve(cls), init_body, cls_locals)
    )
    setattr(cls, "into_call", classmethod(_ss_into_call))

    return cls


def stream(cls: T) -> Union[Callable, T]:
    def wrap(cls: T) -> T:
        setattr(cls, STREAM_TYPE_FIELD, StreamType.STREAM)
        return _process_class(cls)

    if cls is None:
        return wrap

    return wrap(cls)


def section(cls: T) -> Union[Callable, T]:
    def wrap(cls: T) -> T:
        setattr(cls, STREAM_TYPE_FIELD, StreamType.SECTION)
        return _process_class(cls, is_section=True)

    if cls is None:
        return wrap

    return wrap(cls)

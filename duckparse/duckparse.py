import ast
from abc import ABCMeta
from dataclasses import dataclass

from duckparse.reader import Reader

from typing import (
    Any,
    Tuple,
    Union,
    Dict,
    List,
    Callable,
    Optional,
    Iterable,
)

__all__ = [
    "Field",
    "stream_parser",
]

READER_NAME = "self.reader"


@dataclass
class Field:
    name: str
    kind: Any
    params: Any


@dataclass
class Line:
    name: str
    value: Callable
    params: Optional[Tuple] = None


def _create_fn(name, args, body, *, globals=None, locals=None):
    # SOURCE: https://github.com/python/cpython/blob/master/Lib/dataclasses.py
    # Note that we mutate locals when exec() is called.  Caller
    # beware!  The only callers are internal to this module, so no
    # worries about external callers.
    locals = locals or {}
    globals = globals or {}

    args = ",".join(args)
    body = "\n".join(f"  {b}" for b in body)

    # Compute the text of the entire function.
    txt = f" def {name}({args}):\n{body}"

    local_vars = ", ".join(locals.keys())
    txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"

    ns = {}
    exec(txt, globals, ns)
    func = ns["__create_fn__"](**locals)
    for arg, annotation in func.__annotations__.copy().items():
        func.__annotations__[arg] = locals[annotation]
    return func


def _normalize_annotations(annontations: Iterable):
    for elem in annontations:
        name, kind_params = elem
        if isinstance(kind_params, tuple):
            kind, params = kind_params
            yield name, kind, params
        else:
            yield name, kind_params(), None


def _make_repr(cls_name: str, lines: List[Line], cls_locals):
    arguments = ", ".join(
        f"{line.name}={{self.{line.name}!r}}" for line in lines
    )
    function_body = [f"return f'{cls_name}({arguments})'"]
    function = _create_fn(
        "__repr__", ("self",), function_body, locals=cls_locals
    )

    return function


def _make_init(lines: List[Line], cls_locals: Dict[str, Any]):
    def make_line(line: Line, cls_locals: Dict[str, Any]) -> str:
        params = str()
        getter_name = f"__get_{line.name}__"
        cls_locals[getter_name] = line.value

        if line.params:
            par_counter = 0
            params_as_list: List[str] = list()
            for item in line.params:
                if isinstance(
                    item, (int, str, bool, type(Ellipsis), type(None))
                ):
                    params_as_list.append(str(item))
                else:
                    param_name = f"__{line.name}_par{par_counter}__"
                    cls_locals[param_name] = item
                    params_as_list.append(param_name)
                    par_counter += 1
            params = f'({", ".join(params_as_list)},)'

        result = (
            f"self.{line.name} = {getter_name}({READER_NAME}, {params})"
        )
        return result

    cls_locals["Reader"] = Reader
    function_body = (
        f"{READER_NAME} = Reader(io)",
        *(make_line(line_object, cls_locals) for line_object in lines),
    )
    function = _create_fn(
        "__init__", ("self", "io"), function_body, locals=cls_locals
    )

    return function


def _process_class(cls):
    cls_annotations = {}
    if hasattr(cls, "__annotations__"):
        cls_annotations = cls.__annotations__
        del cls.__annotations__

    cls_locals = dict()
    cls_fields = (
        Field(name, kind, params)
        for name, kind, params in _normalize_annotations(
            cls_annotations.items()
        )
    )

    init_body = list()
    reprocessors_dict: Dict[str, List[Tuple[str, Callable]]] = dict()
    for field in cls_fields:
        # TODO: startswith
        # TODO: PADDING
        # TODO: return type
        # TODO: lazy parsing
        if hasattr(field.kind, "__reprocess_after__"):
            reprocessors_dict.setdefault(
                field.kind.__reprocess_after__, []
            ).append(
                (
                    field.kind.__reprocessor_name__,
                    field.kind.__reprocessor__,
                )
            )

        init_body.append(
            Line(field.name, field.kind.__processor__, field.params)
        )

        if reprocessors := reprocessors_dict.get(field.name):
            init_body.extend(
                Line(name, reprocessor, READER_NAME)
                for name, reprocessor in reprocessors
            )

    cls.__init__ = _make_init(init_body, cls_locals)
    cls.__repr__ = _make_repr(cls.__name__, init_body, cls_locals)
    return cls


def stream_parser(cls):
    def wrap(cls):
        return _process_class(cls)

    if cls is None:
        return wrap

    return wrap(cls)

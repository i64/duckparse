from abc import ABCMeta
from dataclasses import dataclass

from .reader import Reader
from .kindprotocol import Kind, VarKind

from .consts import (
    StreamType,
    READER_NAME,
    STREAM_TYPE_FIELD,
    PROCESSOR_FUNCTION_FIELD,
    REPROCESS_AFTER_FIELD,
    REPROCESSOR_FUNCTION_FIELD,
    DATAKIND_GUARD_FIELD,
    REPROCESS_ASSIGN_TO_FIELD,
    PREFUNCTION_FIELD,
)

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


@dataclass
class Call:
    function_name: str
    params: str = ""

    def __repr__(self):
        return f"{self.function_name}({READER_NAME}, {self.params})"


@dataclass
class Assignment:
    value: Call
    assing_to: Optional[str] = None

    def __repr__(self):
        if self.assing_to is not None:
            return f"self.{self.assing_to} = {self.value!r}"
        else:
            return repr(self.value)


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
    # print(txt)

    local_vars = ", ".join(locals.keys())
    txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"
    ns = {}
    exec(txt, globals, ns)
    func = ns["__create_fn__"](**locals)
    for arg, annotation in func.__annotations__.copy().items():
        func.__annotations__[arg] = locals[annotation]
    return func


def _normalize_kind(annontations: Iterable) -> Kind:
    for elem in annontations:
        if isinstance(elem, Kind):
            yield elem
        elif (
            hasattr(elem, STREAM_TYPE_FIELD)
            and getattr(elem, STREAM_TYPE_FIELD) is StreamType.SECTION
        ):
            yield Kind(instance=elem, params=None)
        else:
            yield Kind(
                instance=elem(), params=None,
            )


def _make_repr(cls_name: str, assigments: List[Assignment], cls_locals):
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
):
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


def _process_class(cls, is_section: bool = False):
    if hasattr(cls, "__annotations__"):
        cls_annotations = cls.__annotations__
        del cls.__annotations__
    else:
        # TODO: Raise an error
        ...
    cls_locals: Dict[str, Any] = dict()

    init_body: List[Assignment] = list()
    reprocessors_dict: Dict[str, List[Tuple[str, Assignment]]] = dict()

    if hasattr(cls, PREFUNCTION_FIELD):
        prefunction = getattr(cls, PREFUNCTION_FIELD)
        cls_locals[prefunction.__name__] = prefunction
        init_body.append(
            Assignment(
                value=Call(function_name=f"self.{prefunction.__name__}",)
            )
        )

    for field_name, kind in zip(
        cls_annotations.keys(), _normalize_kind(cls_annotations.values()),
    ):
        call = get_call(
            kind,
            cls_locals=cls_locals,
            reprocessors_dict=reprocessors_dict,
        )
        init_body.append(Assignment(assing_to=field_name, value=call))
        if reprocessor := reprocessors_dict.get(field_name):
            init_body.extend(reprocessor)

    cls.__init__ = _make_init(init_body, cls_locals, is_section)
    cls.__repr__ = _make_repr(cls.__name__, init_body, cls_locals)
    return cls


#         ...
def get_call(
    kind: Kind,
    cls_locals: Dict[str, Any],
    par_counter: Optional[List[int]] = None,
    reprocessors_dict: Optional[Dict[str, Assignment]] = None,
) -> Call:

    if not hasattr(kind, PROCESSOR_FUNCTION_FIELD):
        # TODO: raise error: missing field
        ...
    params = ""
    par_counter = par_counter or [0]

    field_name = kind.instance.__class__.__name__

    if hasattr(kind.instance, REPROCESS_AFTER_FIELD) and hasattr(
        kind.instance, REPROCESS_ASSIGN_TO_FIELD
    ):
        function_name = f"__duckparse_function_{getattr(kind.instance, REPROCESS_AFTER_FIELD)}_{par_counter[0]}__"
        reprocessors_dict.setdefault(
            getattr(kind.instance, REPROCESS_AFTER_FIELD), []
        ).append(
            Assignment(
                value=Call(function_name=function_name, params="(self,)"),
                assing_to=getattr(
                    kind.instance, REPROCESS_ASSIGN_TO_FIELD
                ),
            )
        )
        cls_locals[function_name] = getattr(
            kind.instance, REPROCESSOR_FUNCTION_FIELD
        )
        par_counter[0] += 1
    if (
        hasattr(kind.instance, STREAM_TYPE_FIELD)
        and getattr(kind.instance, STREAM_TYPE_FIELD)
        is StreamType.SECTION
    ):
        function_name = f"__duckparse_function_{kind.instance.__name__}__"
        cls_locals[function_name] = kind.instance
        return Call(function_name=function_name,)

    else:
        if kind.params:
            params_as_list: List[str] = list()
            for item in kind.params:
                if isinstance(
                    item,
                    (
                        int,
                        str,
                        bool,
                        bytes,
                        bytearray,
                        VarKind,
                        type(Ellipsis),
                        type(None),
                    ),
                ):
                    params_as_list.append(item)
                elif isinstance(item, Kind) or hasattr(
                    item, DATAKIND_GUARD_FIELD
                ):
                    if hasattr(
                        item, DATAKIND_GUARD_FIELD
                    ) and not isinstance(item, Kind):
                        item = Kind(instance=item(), params=None,)

                    params_as_list.append(
                        get_call(
                            kind=item,
                            par_counter=par_counter,
                            cls_locals=cls_locals,
                            reprocessors_dict=reprocessors_dict,
                        )
                    )
                    par_counter[0] += 1
                else:
                    param_name = f"__{field_name}_par{par_counter[0]}__"
                    cls_locals[param_name] = item
                    params_as_list.append(param_name)
                    par_counter[0] += 1
            params = f'({", ".join(map(repr, params_as_list))},)'

    function_name = (
        f"__duckparse_function_{field_name}_{par_counter[0]}__"
    )
    cls_locals[function_name] = getattr(
        kind.instance, PROCESSOR_FUNCTION_FIELD
    )
    return Call(function_name=function_name, params=params,)


def stream(cls):
    def wrap(cls):
        setattr(cls, STREAM_TYPE_FIELD, StreamType.STREAM)
        return _process_class(cls)

    if cls is None:
        return wrap

    return wrap(cls)


def section(cls):
    def wrap(cls):
        setattr(cls, STREAM_TYPE_FIELD, StreamType.SECTION)
        return _process_class(cls, is_section=True)

    if cls is None:
        return wrap

    return wrap(cls)

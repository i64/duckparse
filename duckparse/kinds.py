from enum import Enum
from dataclasses import dataclass

from .utils import generic_repeat, whilor, resolve

from .reader import Reader
from .kindprotocol import Kind, Assignment, Call

from .consts import (
    ENUM_FIELD,
    DATAKIND_GUARD_FIELD,
    REPROCESS_AFTER_FIELD,
    REPROCESS_ASSIGN_TO_FIELD,
    REPROCESSOR_FUNCTION_FIELD,
    PROCESSOR_FUNCTION_FIELD,
)

from typing import (
    Tuple,
    List,
    Callable,
    Optional,
    Dict,
    Any,
    Union,
    TypeVar,
)

T = TypeVar("T")


@dataclass
class VarKind(Kind):
    var_name: str

    def __repr__(self) -> str:
        return f"self.{self.var_name}"


@dataclass
class DataKind(Kind):
    base_cls: Any
    params: Optional[Tuple[Any]] = None
    kind_locals: Optional[Dict[str, Any]] = None

    def __getitem__(self: "DataKind", params) -> "DataKind":
        if not isinstance(params, tuple):
            params = (params,)

        return DataKind(
            base_cls=self.base_cls,
            params=params,
            kind_locals=self.kind_locals,
        )

    def into_call(
        self,
        cls_locals: Dict[str, Any],
        par_counter: Optional[List[int]] = None,
        reprocessors_dict: Optional[Dict[str, List[Assignment]]] = None,
    ) -> Call:
        if par_counter is None:
            par_counter = [0]
        if reprocessors_dict is None:
            reprocessors_dict = dict()

        kind_name = resolve(self.base_cls)
        params = ""

        if hasattr(self.base_cls, REPROCESS_AFTER_FIELD) and hasattr(
            self.base_cls, REPROCESS_ASSIGN_TO_FIELD
        ):
            function_name = f"__duckparse_function_{getattr(self.base_cls, REPROCESS_AFTER_FIELD)}_{par_counter[0]}__"
            reprocessors_dict.setdefault(
                getattr(self.base_cls, REPROCESS_AFTER_FIELD), []
            ).append(
                Assignment(
                    value=Call(
                        function_name=function_name, params="(self,)"
                    ),
                    assing_to=getattr(
                        self.base_cls, REPROCESS_ASSIGN_TO_FIELD
                    ),
                )
            )
            cls_locals[function_name] = getattr(
                self.base_cls, REPROCESSOR_FUNCTION_FIELD
            )
            par_counter[0] += 1

        if self.params:
            params_as_list = list()
            for item in self.params:
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
                        item = item()

                    params_as_list.append(
                        item.into_call(
                            cls_locals,
                            par_counter=par_counter,
                            reprocessors_dict=reprocessors_dict,
                        )
                    )
                    par_counter[0] += 1
                else:
                    param_name = f"__{kind_name}_par{par_counter[0]}__"
                    cls_locals[param_name] = item
                    par_counter[0] += 1
                    params_as_list.append(param_name)

            params = f'({", ".join(map(repr, params_as_list))},)'

        instance = self.base_cls()
        function_name = (
            f"__duckparse_function_{kind_name}_{par_counter[0]}__"
        )
        cls_locals[function_name] = getattr(
            instance, PROCESSOR_FUNCTION_FIELD
        )

        return Call(function_name=function_name, params=params,)


def datakind(cls) -> Union[Callable, DataKind]:
    def wrap(cls) -> DataKind:
        setattr(cls, DATAKIND_GUARD_FIELD, True)
        return DataKind(base_cls=cls)

    if cls is None:
        return wrap

    return wrap(cls)


def __enum__preprocessor__(
    self, reader: Reader, params: Tuple[int]
) -> Enum:
    (idx,) = params
    return self.__masked_enum__(idx)


def enumkind(cls) -> Union[Callable, DataKind]:
    def wrap(cls) -> DataKind:
        setattr(cls, ENUM_FIELD, Enum(cls.__name__, cls.__dict__))
        setattr(
            getattr(cls, ENUM_FIELD),
            "__repr__",
            getattr(getattr(cls, ENUM_FIELD), "__str__"),
        )  # mypy...
        setattr(cls, PROCESSOR_FUNCTION_FIELD, __enum__preprocessor__)
        return datakind(cls)  # type: ignore

    if cls is None:
        return wrap

    return wrap(cls)


@dataclass
class RepeatKind(Kind):
    condition: str
    body: Kind
    kind_locals: Optional[Dict[str, Any]] = None

    def into_call(
        self,
        cls_locals: Dict[str, Any],
        par_counter: Optional[List[int]] = None,
        reprocessors_dict: Optional[Dict[str, List[Assignment]]] = None,
    ) -> Call:
        if par_counter is None:
            par_counter = [0]
        if self.kind_locals is not None:
            cls_locals.update(self.kind_locals)

        function_name = "__duckparse_generic_repeat__"
        cls_locals[function_name] = generic_repeat

        new_body = self.body.into_call(
            cls_locals=cls_locals,
            par_counter=par_counter,
            reprocessors_dict=reprocessors_dict,
        )

        return Call(
            function_name=function_name,
            params=f"lambda: {new_body!r}, {self.condition}",
            reader_as_param=False,
        )


class RepeatN(RepeatKind):
    def __class_getitem__(cls, params: Tuple[Kind, str]):
        assert isinstance(params, tuple)
        assert len(params) == 2
        body, condition = params
        return cls(condition=condition, body=body)


class RepeatEOS(RepeatKind):
    def __class_getitem__(cls, body: Kind):
        return cls(
            condition="whilor(lambda: self.reader.io.tell() != self.reader.size)",
            body=body,
            kind_locals={"whilor": whilor},
        )

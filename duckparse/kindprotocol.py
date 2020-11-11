from dataclasses import dataclass

from .consts import READER_NAME

from typing import (
    Optional,
    Any,
    Dict,
    Protocol,
    List,
    Tuple,
    runtime_checkable,
)


@dataclass
class Call:
    function_name: str
    params: str = ""
    reader_as_param: bool = True

    def __repr__(self) -> str:
        if self.reader_as_param:
            return f"{self.function_name}({READER_NAME}, {self.params})"
        return f"{self.function_name}({self.params})"


@dataclass
class Assignment:
    value: Call
    assing_to: Optional[str] = None

    def __repr__(self) -> str:
        if self.assing_to is not None:
            return f"self.{self.assing_to} = {self.value!r}"
        else:
            return repr(self.value)


@runtime_checkable
class Kind(Protocol):
    kind_locals: Optional[Dict[str, Any]] = None

    def into_call(
        self,
        cls_locals: Dict[str, Any],
        par_counter: Optional[List[int]] = None,
        reprocessors_dict: Optional[Dict[str, List[Assignment]]] = None,
    ) -> Call:
        ...

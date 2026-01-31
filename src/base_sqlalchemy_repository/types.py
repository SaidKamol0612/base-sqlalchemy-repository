from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Literal,
    TypeAlias,
    TypeVar,
    Union,
)

from sqlalchemy import ColumnElement
from sqlalchemy.orm import DeclarativeBase


M = TypeVar("M", bound=DeclarativeBase)
Numeric = Union[float, int]

Column = ColumnElement[Any]

BinaryOp = Callable[[Column, Any], ColumnElement[bool]]
NumericOp = Callable[[ColumnElement[Numeric], Numeric], ColumnElement[bool]]
StringOp = Callable[[ColumnElement[str], str], ColumnElement[bool]]
InclusionOp = Callable[[Column, Collection[Any]], ColumnElement[bool]]

FilterOperator: TypeAlias = Literal[
    "eq",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "like",
    "ilike",
    "in_",
]
FilterAction = Union[BinaryOp, NumericOp, StringOp, InclusionOp]
SQLOperationsDict = Dict[FilterOperator, FilterAction]

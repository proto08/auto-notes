from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_S = TypeVar("_S")
_T = TypeVar("_T")


def dict_factory() -> Dict[str, Any]:
    return {}


def list_factory() -> List[Any]:
    return []


EMPTY_UUID = UUID("00000000-0000-0000-0000-000000000000")


class BaseResponse(BaseModel):
    message: str = "OK"


class BaseDto(BaseModel):
    """DTOの基底クラス"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_encoders={datetime: lambda value: value.isoformat()},
    )


class TypedResponse(BaseResponse, Generic[_T]):
    """単一の値を返すレスポンス"""

    item: _T
    message: str = "OK"


class TypedListResponse(BaseResponse, Generic[_T]):
    """複数の値を返すレスポンス"""

    items: List[_T]

    @staticmethod
    def from_models(
        models: List[_S], converter: Callable[[_S], _T], message: str = "OK"
    ) -> "TypedListResponse[_T]":
        """モデル一覧からTypedListResponseを構成する"""
        items = list[_T](
            map[_T](
                lambda item: converter(item),
                models,
            )
        )
        return TypedListResponse[_T](items=items, message=message)


class SearchResponse(TypedListResponse[_T]):
    count: int = Field(description="取得可能な最大項目数")

    @staticmethod
    def from_models(
        models: List[_S],
        converter: Callable[[_S], _T],
        message: str = "OK",
        count: int = 0,
    ) -> "SearchResponse[_T]":
        """モデル一覧からSearchResponseを構成する"""
        items = list[_T](
            map[_T](
                lambda item: converter(item),
                models,
            )
        )
        return SearchResponse[_T](count=count, items=items, message=message)

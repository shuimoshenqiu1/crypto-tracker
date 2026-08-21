from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = ""


def success_response(data: Any = None, message: str = "") -> dict:
    return {"code": 0, "data": data, "message": message}


def error_response(code: int, message: str) -> dict:
    return {"code": code, "data": None, "message": message}

from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if len(v) > 72:
            raise ValueError("密码长度不能超过72位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含至少一个数字")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 1:
            raise ValueError("名称不能为空")
        if len(v) > 100:
            raise ValueError("名称不能超过100个字符")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: int  # Unix ms


class UserMeResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: int  # Unix ms


class UserLoginUserInfo(BaseModel):
    id: str
    email: str
    name: str
    role: str


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: UserLoginUserInfo

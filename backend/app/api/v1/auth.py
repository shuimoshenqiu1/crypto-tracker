from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.crud.user import create_user, get_user_by_email
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import error_response, success_response
from app.schemas.user import UserLoginRequest, UserRegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(40901, "邮箱已被注册"),
        )
    user = await create_user(db, email=body.email, password=body.password, name=body.name)
    return success_response(
        data={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": int(user.created_at.timestamp() * 1000),
        }
    )


@router.post("/login")
async def login(
    body: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(40101, "邮箱或密码错误"),
        )
    token = create_access_token(str(user.id), user.email, user.role)
    return success_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }
    )


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> dict:
    return success_response(
        data={
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": int(current_user.created_at.timestamp() * 1000),
        }
    )

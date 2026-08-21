from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud.coin import get_coin_by_id
from app.crud.watchlist import (
    add_to_watchlist,
    count_watchlist,
    get_watchlist,
    get_watchlist_item,
    remove_from_watchlist,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import error_response

router = APIRouter(tags=["watchlist"])

MAX_WATCHLIST_SIZE = 50


class AddWatchlistRequest(BaseModel):
    coin_id: str


@router.get("/watchlist")
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items = await get_watchlist(db, current_user.id)
    return {"code": 0, "data": {"items": items, "total": len(items)}, "message": ""}


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
async def add_watchlist(
    body: AddWatchlistRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Check coin exists
    coin = await get_coin_by_id(db, body.coin_id)
    if coin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, "币种不存在"),
        )

    # Check duplicate
    existing = await get_watchlist_item(db, current_user.id, body.coin_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(40901, "该币种已在自选列表中"),
        )

    # Check max limit
    count = await count_watchlist(db, current_user.id)
    if count >= MAX_WATCHLIST_SIZE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(40901, f"自选列表最多 {MAX_WATCHLIST_SIZE} 个币种"),
        )

    item = await add_to_watchlist(db, current_user.id, body.coin_id, sort_order=count)
    return {
        "code": 0,
        "data": {
            "coin_id": item.coin_id,
            "sort_order": item.sort_order,
            "added_at": int(item.added_at.timestamp() * 1000),
        },
        "message": "",
    }


@router.delete("/watchlist/{coin_id}")
async def delete_watchlist(
    coin_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    deleted = await remove_from_watchlist(db, current_user.id, coin_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, "该币种不在自选列表中"),
        )
    return {"code": 0, "data": None, "message": ""}

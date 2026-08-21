from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud.coin import get_coin_by_id, get_coins
from app.db.session import get_db
from app.models.user import User
from app.schemas.coin import CoinDetail, CoinListItem
from app.schemas.common import error_response, success_response
from app.services.cache import get_cached, set_cached

import json

router = APIRouter(tags=["coins"])


@router.get("/coins")
async def list_coins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("market_cap_rank"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Try cache first (only for non-search requests)
    cache_key = None
    if not search:
        cache_key = f"coins:list:{page}:{page_size}:{sort_by}:{sort_order}"
        cached = await get_cached(cache_key)
        if cached:
            return json.loads(cached)

    items, total = await get_coins(
        db, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order, search=search
    )

    items_data = [CoinListItem.model_validate(item).model_dump() for item in items]

    response = success_response(
        data={
            "items": items_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )

    # Cache for 60 seconds (only non-search results)
    if cache_key:
        await set_cached(cache_key, json.dumps(response), ttl=60)
    return response


@router.get("/coins/{coin_id}")
async def get_coin_detail(
    coin_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    coin = await get_coin_by_id(db, coin_id)
    if coin is None:
        raise HTTPException(
            status_code=404,
            detail=error_response(40401, "币种不存在"),
        )

    detail = CoinDetail.from_model(coin)
    return success_response(data=detail.model_dump())

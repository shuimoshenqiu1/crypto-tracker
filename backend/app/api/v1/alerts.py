from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud.alert import (
    count_active_alerts,
    create_alert,
    delete_alert,
    get_alert_by_id,
    get_alert_history,
    get_alerts,
    update_alert,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import error_response, success_response

router = APIRouter(prefix="/alerts", tags=["alerts"])

VALID_CONDITION_TYPES = {"price_above", "price_below", "pct_change_above", "pct_change_below"}
MAX_ACTIVE_ALERTS = 20


# --- Request/Response Schemas ---


class AlertCreateRequest(BaseModel):
    coin_id: str = Field(..., min_length=1)
    condition_type: str = Field(...)
    threshold: float = Field(..., gt=0)
    is_repeating: bool = False
    cooldown_secs: int = Field(default=3600, ge=60)


class AlertUpdateRequest(BaseModel):
    threshold: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None
    is_repeating: Optional[bool] = None
    cooldown_secs: Optional[int] = Field(default=None, ge=60)


# --- Helper to format alert response ---


def _format_alert(alert) -> dict:
    return {
        "id": str(alert.id),
        "coin_id": alert.coin_id,
        "condition_type": alert.condition_type,
        "threshold": float(alert.threshold),
        "is_active": alert.is_active,
        "is_repeating": alert.is_repeating,
        "cooldown_secs": alert.cooldown_secs,
        "last_triggered": int(alert.last_triggered.timestamp() * 1000) if alert.last_triggered else None,
        "created_at": int(alert.created_at.timestamp() * 1000),
        "updated_at": int(alert.updated_at.timestamp() * 1000),
    }


def _format_history(h) -> dict:
    return {
        "id": str(h.id),
        "alert_id": str(h.alert_id),
        "coin_id": h.coin_id,
        "coin_symbol": h.coin_symbol,
        "condition_type": h.condition_type,
        "threshold": float(h.threshold),
        "trigger_price": float(h.trigger_price),
        "message": h.message,
        "triggered_at": int(h.triggered_at.timestamp() * 1000),
    }


# --- Endpoints ---


@router.get("")
async def list_alerts(
    is_active: Optional[bool] = Query(default=None),
    coin_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await get_alerts(
        db,
        current_user.id,
        is_active=is_active,
        coin_id=coin_id,
        page=page,
        page_size=page_size,
    )
    return success_response({
        "items": [_format_alert(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert_endpoint(
    body: AlertCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Validate condition_type
    if body.condition_type not in VALID_CONDITION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(42201, f"无效的 condition_type: {body.condition_type}"),
        )

    # Check coin exists
    from app.crud.coin import get_coin_by_id

    coin = await get_coin_by_id(db, body.coin_id)
    if coin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, f"币种 {body.coin_id} 不存在"),
        )

    # Check max active alerts
    active_count = await count_active_alerts(db, current_user.id)
    if active_count >= MAX_ACTIVE_ALERTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(40001, f"活跃告警数量已达上限 ({MAX_ACTIVE_ALERTS})"),
        )

    alert = await create_alert(
        db,
        user_id=current_user.id,
        coin_id=body.coin_id,
        condition_type=body.condition_type,
        threshold=body.threshold,
        is_repeating=body.is_repeating,
        cooldown_secs=body.cooldown_secs,
    )
    return success_response(_format_alert(alert))


@router.patch("/{alert_id}")
async def update_alert_endpoint(
    alert_id: uuid.UUID,
    body: AlertUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    alert = await get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, "告警不存在"),
        )
    if alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(40301, "无权操作此告警"),
        )

    updated = await update_alert(
        db,
        alert,
        threshold=body.threshold,
        is_active=body.is_active,
        is_repeating=body.is_repeating,
        cooldown_secs=body.cooldown_secs,
    )
    return success_response(_format_alert(updated))


@router.delete("/{alert_id}")
async def delete_alert_endpoint(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    alert = await get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, "告警不存在"),
        )
    if alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(40301, "无权操作此告警"),
        )

    await delete_alert(db, alert)
    return success_response(None)


@router.get("/history")
async def list_alert_history(
    coin_id: Optional[str] = Query(default=None),
    start_time: Optional[int] = Query(default=None),
    end_time: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await get_alert_history(
        db,
        current_user.id,
        coin_id=coin_id,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    return success_response({
        "items": [_format_history(h) for h in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })

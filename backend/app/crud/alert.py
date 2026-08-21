from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.alert_history import AlertHistory


async def get_alerts(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    is_active: bool | None = None,
    coin_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Alert], int]:
    """Get paginated alerts for a user with optional filters."""
    query = select(Alert).where(Alert.user_id == user_id)
    count_query = select(func.count()).select_from(Alert).where(Alert.user_id == user_id)

    if is_active is not None:
        query = query.where(Alert.is_active == is_active)
        count_query = count_query.where(Alert.is_active == is_active)
    if coin_id is not None:
        query = query.where(Alert.coin_id == coin_id)
        count_query = count_query.where(Alert.coin_id == coin_id)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Alert.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())
    return items, total


async def get_alert_by_id(db: AsyncSession, alert_id: uuid.UUID) -> Alert | None:
    """Get a single alert by ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    return result.scalar_one_or_none()


async def count_active_alerts(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Count active alerts for a user."""
    result = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(Alert.user_id == user_id, Alert.is_active == True)  # noqa: E712
    )
    return result.scalar() or 0


async def create_alert(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    coin_id: str,
    condition_type: str,
    threshold: float,
    is_repeating: bool = False,
    cooldown_secs: int = 3600,
) -> Alert:
    """Create a new alert."""
    alert = Alert(
        user_id=user_id,
        coin_id=coin_id,
        condition_type=condition_type,
        threshold=threshold,
        is_repeating=is_repeating,
        cooldown_secs=cooldown_secs,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


async def update_alert(
    db: AsyncSession,
    alert: Alert,
    *,
    threshold: float | None = None,
    is_active: bool | None = None,
    is_repeating: bool | None = None,
    cooldown_secs: int | None = None,
) -> Alert:
    """Update an existing alert."""
    if threshold is not None:
        alert.threshold = threshold
    if is_active is not None:
        alert.is_active = is_active
    if is_repeating is not None:
        alert.is_repeating = is_repeating
    if cooldown_secs is not None:
        alert.cooldown_secs = cooldown_secs
    alert.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(alert)
    return alert


async def delete_alert(db: AsyncSession, alert: Alert) -> None:
    """Delete an alert."""
    await db.delete(alert)
    await db.flush()


async def get_alert_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    coin_id: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AlertHistory], int]:
    """Get paginated alert history for a user."""
    query = select(AlertHistory).where(AlertHistory.user_id == user_id)
    count_query = (
        select(func.count())
        .select_from(AlertHistory)
        .where(AlertHistory.user_id == user_id)
    )

    if coin_id is not None:
        query = query.where(AlertHistory.coin_id == coin_id)
        count_query = count_query.where(AlertHistory.coin_id == coin_id)
    if start_time is not None:
        start_dt = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
        query = query.where(AlertHistory.triggered_at >= start_dt)
        count_query = count_query.where(AlertHistory.triggered_at >= start_dt)
    if end_time is not None:
        end_dt = datetime.fromtimestamp(end_time / 1000, tz=timezone.utc)
        query = query.where(AlertHistory.triggered_at <= end_dt)
        count_query = count_query.where(AlertHistory.triggered_at <= end_dt)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(AlertHistory.triggered_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())
    return items, total

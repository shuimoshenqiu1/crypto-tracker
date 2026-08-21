from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest import BacktestJob


async def create_job(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    coin_id: str,
    strategy_name: str,
    params: dict,
    interval: str,
    start_time: int,
    end_time: int,
) -> BacktestJob:
    """Create a new backtest job in pending status."""
    job = BacktestJob(
        user_id=user_id,
        coin_id=coin_id,
        strategy_name=strategy_name,
        params=params,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        status="pending",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID) -> BacktestJob | None:
    """Get a backtest job by ID."""
    result = await db.execute(select(BacktestJob).where(BacktestJob.id == job_id))
    return result.scalar_one_or_none()


async def update_job_status(
    db: AsyncSession,
    job: BacktestJob,
    *,
    status: str,
    result: dict | None = None,
    error_message: str | None = None,
) -> BacktestJob:
    """Update backtest job status and optionally result/error."""
    job.status = status
    if result is not None:
        job.result = result
    if error_message is not None:
        job.error_message = error_message
    if status in ("completed", "failed"):
        job.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(job)
    return job


async def get_user_jobs(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 20,
) -> list[BacktestJob]:
    """Get backtest jobs for a user, ordered by created_at descending."""
    query = (
        select(BacktestJob)
        .where(BacktestJob.user_id == user_id)
        .order_by(BacktestJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

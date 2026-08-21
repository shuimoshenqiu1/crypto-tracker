from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.backtest import BacktestJob
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _execute_backtest(job_id: str) -> None:
    """Async implementation of backtest execution."""
    from app.services.backtest_engine import run_backtest

    engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=2, max_overflow=0)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    job_uuid = uuid.UUID(job_id)

    try:
        # Read job params
        async with session_factory() as db:
            result = await db.execute(
                select(BacktestJob).where(BacktestJob.id == job_uuid)
            )
            job = result.scalar_one_or_none()
            if job is None:
                logger.error(f"Backtest job {job_id} not found")
                return

            # Update status to running
            job.status = "running"
            await db.commit()

            # Store params before closing session
            coin_id = job.coin_id
            strategy_name = job.strategy_name
            params = job.params
            interval = job.interval
            start_time = job.start_time
            end_time = job.end_time

        # Run the actual backtest
        backtest_result = await run_backtest(
            coin_id=coin_id,
            strategy_name=strategy_name,
            params=params,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )

        # Update job with results
        async with session_factory() as db:
            result = await db.execute(
                select(BacktestJob).where(BacktestJob.id == job_uuid)
            )
            job = result.scalar_one_or_none()
            if job:
                job.status = "completed"
                job.result = backtest_result
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

        logger.info(f"Backtest job {job_id} completed successfully")

    except Exception as e:
        logger.exception(f"Backtest job {job_id} failed: {e}")
        try:
            async with session_factory() as db:
                result = await db.execute(
                    select(BacktestJob).where(BacktestJob.id == job_uuid)
                )
                job = result.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)[:500]
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update job status: {db_err}")
    finally:
        await engine.dispose()


@celery_app.task(
    name="app.tasks.run_backtest.run_backtest_task",
    soft_time_limit=300,
    time_limit=360,
    max_retries=0,
)
def run_backtest_task(job_id: str) -> str:
    """Celery task: execute a backtest job."""
    asyncio.run(_execute_backtest(job_id))
    return f"Backtest {job_id} processed"

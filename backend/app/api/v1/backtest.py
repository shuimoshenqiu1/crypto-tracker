from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud.backtest import create_job, get_job_by_id
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import error_response, success_response

router = APIRouter(prefix="/backtest", tags=["backtest"])

VALID_STRATEGIES = ["ma_cross", "rsi", "bollinger"]
VALID_INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]


# --- Request/Response schemas ---


class BacktestRunRequest(BaseModel):
    coin_id: str = Field(..., min_length=1)
    strategy_name: str = Field(...)
    params: dict = Field(default_factory=dict)
    interval: str = Field(default="1h")
    start_time: int = Field(...)
    end_time: int = Field(...)


# --- Endpoints ---


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def submit_backtest(
    body: BacktestRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Submit a backtest job (async execution via Celery)."""
    # Validate strategy_name
    if body.strategy_name not in VALID_STRATEGIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(40001, f"无效策略名: {body.strategy_name}，可选: {VALID_STRATEGIES}"),
        )

    # Validate interval
    if body.interval not in VALID_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(40001, f"无效K线周期: {body.interval}"),
        )

    # Validate time range
    if body.start_time >= body.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(40001, "start_time 必须小于 end_time"),
        )

    # Create job in DB
    job = await create_job(
        db,
        user_id=current_user.id,
        coin_id=body.coin_id,
        strategy_name=body.strategy_name,
        params=body.params,
        interval=body.interval,
        start_time=body.start_time,
        end_time=body.end_time,
    )

    # Dispatch Celery task
    from app.tasks.run_backtest import run_backtest_task

    run_backtest_task.delay(str(job.id))

    return success_response(
        data={
            "job_id": str(job.id),
            "status": "pending",
            "created_at": int(job.created_at.timestamp() * 1000),
        }
    )


@router.get("/{job_id}")
async def get_backtest_result(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get backtest job status and result."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, "job_id 格式无效"),
        )

    job = await get_job_by_id(db, job_uuid)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(40401, "回测任务不存在"),
        )

    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(40301, "非本人任务"),
        )

    data: dict = {
        "job_id": str(job.id),
        "coin_id": job.coin_id,
        "strategy_name": job.strategy_name,
        "params": job.params,
        "interval": job.interval,
        "start_time": job.start_time,
        "end_time": job.end_time,
        "status": job.status,
        "result": job.result,
        "created_at": int(job.created_at.timestamp() * 1000),
        "completed_at": int(job.completed_at.timestamp() * 1000) if job.completed_at else None,
    }

    if job.status == "failed":
        data["error_message"] = job.error_message

    return success_response(data=data)


@router.get("/strategies", name="backtest_strategies")
async def list_strategies(
    current_user: User = Depends(get_current_user),
) -> dict:
    """List available backtest strategies with parameter schemas."""
    strategies = [
        {
            "name": "ma_cross",
            "display_name": "均线交叉策略",
            "description": "短期均线上穿长期均线时买入，下穿时卖出",
            "params_schema": {
                "short_period": {
                    "type": "int",
                    "min": 2,
                    "max": 50,
                    "default": 7,
                    "description": "短期均线周期",
                },
                "long_period": {
                    "type": "int",
                    "min": 10,
                    "max": 200,
                    "default": 25,
                    "description": "长期均线周期",
                },
            },
        },
        {
            "name": "rsi",
            "display_name": "RSI 超买超卖策略",
            "description": "RSI 低于超卖线买入，高于超买线卖出",
            "params_schema": {
                "period": {
                    "type": "int",
                    "min": 5,
                    "max": 50,
                    "default": 14,
                    "description": "RSI 计算周期",
                },
                "oversold": {
                    "type": "float",
                    "min": 10,
                    "max": 40,
                    "default": 30,
                    "description": "超卖阈值",
                },
                "overbought": {
                    "type": "float",
                    "min": 60,
                    "max": 90,
                    "default": 70,
                    "description": "超买阈值",
                },
            },
        },
        {
            "name": "bollinger",
            "display_name": "布林带策略",
            "description": "价格触及下轨买入，触及上轨卖出",
            "params_schema": {
                "period": {
                    "type": "int",
                    "min": 10,
                    "max": 50,
                    "default": 20,
                    "description": "布林带周期",
                },
                "std_dev": {
                    "type": "float",
                    "min": 1.0,
                    "max": 3.0,
                    "default": 2.0,
                    "description": "标准差倍数",
                },
            },
        },
    ]
    return success_response(data={"strategies": strategies})

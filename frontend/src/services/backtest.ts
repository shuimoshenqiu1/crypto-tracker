import api from './api';
import type { ApiResponse, BacktestJob, CreateBacktestRequest, StrategiesResponse } from '../types/api';

export async function submitBacktest(data: CreateBacktestRequest) {
  const res = await api.post<ApiResponse<{ job_id: string; status: string; created_at: number }>>('/backtest/run', data);
  return res.data;
}

export async function getBacktestResult(jobId: string) {
  const res = await api.get<ApiResponse<BacktestJob>>(`/backtest/${jobId}`);
  return res.data;
}

export async function getStrategies() {
  const res = await api.get<ApiResponse<StrategiesResponse>>('/backtest/strategies');
  return res.data;
}

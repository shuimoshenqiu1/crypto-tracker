import api from './api';
import type { ApiResponse, KlineResponse } from '../types/api';

export interface KlineParams {
  interval: string;
  start_time: number;
  end_time: number;
  limit?: number;
}

export async function getKlines(coinId: string, params: KlineParams) {
  const res = await api.get<ApiResponse<KlineResponse>>(`/coins/${coinId}/klines`, { params });
  return res.data;
}

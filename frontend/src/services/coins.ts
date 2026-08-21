import api from './api';
import type { ApiResponse, CoinListItem, PaginatedResponse } from '../types/api';

export interface CoinsParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  search?: string;
}

export async function getCoins(params: CoinsParams = {}) {
  const res = await api.get<ApiResponse<PaginatedResponse<CoinListItem>>>('/coins', { params });
  return res.data;
}

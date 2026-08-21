import api from './api';
import type { ApiResponse, WatchlistResponse, WatchlistAddResponse } from '../types/api';

export async function getWatchlist() {
  const res = await api.get<ApiResponse<WatchlistResponse>>('/watchlist');
  return res.data;
}

export async function addToWatchlist(coinId: string) {
  const res = await api.post<ApiResponse<WatchlistAddResponse>>('/watchlist', {
    coin_id: coinId,
  });
  return res.data;
}

export async function removeFromWatchlist(coinId: string) {
  const res = await api.delete<ApiResponse<null>>(`/watchlist/${coinId}`);
  return res.data;
}

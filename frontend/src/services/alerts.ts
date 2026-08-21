import api from './api';
import type {
  ApiResponse,
  PaginatedResponse,
  AlertItem,
  AlertHistoryItem,
  CreateAlertRequest,
  UpdateAlertRequest,
} from '../types/api';

export async function getAlerts(params?: {
  is_active?: boolean;
  coin_id?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<AlertItem>> {
  const res = await api.get<ApiResponse<PaginatedResponse<AlertItem>>>('/alerts', { params });
  return res.data.data;
}

export async function createAlert(data: CreateAlertRequest): Promise<AlertItem> {
  const res = await api.post<ApiResponse<AlertItem>>('/alerts', data);
  return res.data.data;
}

export async function updateAlert(alertId: string, data: UpdateAlertRequest): Promise<AlertItem> {
  const res = await api.patch<ApiResponse<AlertItem>>(`/alerts/${alertId}`, data);
  return res.data.data;
}

export async function deleteAlert(alertId: string): Promise<void> {
  await api.delete(`/alerts/${alertId}`);
}

export async function getAlertHistory(params?: {
  coin_id?: string;
  start_time?: number;
  end_time?: number;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<AlertHistoryItem>> {
  const res = await api.get<ApiResponse<PaginatedResponse<AlertHistoryItem>>>('/alerts/history', { params });
  return res.data.data;
}

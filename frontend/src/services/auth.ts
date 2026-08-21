import api from './api';
import type { ApiResponse, LoginResponseData, RegisterResponseData, UserData } from '../types/api';

export async function register(email: string, password: string, name: string) {
  const res = await api.post<ApiResponse<RegisterResponseData>>('/auth/register', {
    email,
    password,
    name,
  });
  return res.data;
}

export async function login(email: string, password: string) {
  const res = await api.post<ApiResponse<LoginResponseData>>('/auth/login', {
    email,
    password,
  });
  return res.data;
}

export async function getMe() {
  const res = await api.get<ApiResponse<UserData>>('/auth/me');
  return res.data;
}

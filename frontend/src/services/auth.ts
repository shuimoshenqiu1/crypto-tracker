import api from './api';
import { ApiResponse, LoginResponse } from '../types/api';
import { User } from '../types/user';

interface RegisterPayload {
  email: string;
  password: string;
  username: string;
}

interface LoginPayload {
  email: string;
  password: string;
}

export async function register(payload: RegisterPayload): Promise<ApiResponse<User>> {
  const { data } = await api.post<ApiResponse<User>>('/auth/register', payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<ApiResponse<LoginResponse>> {
  const { data } = await api.post<ApiResponse<LoginResponse>>('/auth/login', payload);
  return data;
}

export async function getMe(): Promise<ApiResponse<User>> {
  const { data } = await api.get<ApiResponse<User>>('/auth/me');
  return data;
}

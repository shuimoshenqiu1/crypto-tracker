export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

export interface UserData {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active?: boolean;
  created_at?: number;
}

export interface LoginResponseData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

export interface RegisterResponseData {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: number;
}

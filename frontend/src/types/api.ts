export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

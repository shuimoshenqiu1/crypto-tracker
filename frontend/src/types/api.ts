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

export interface CoinListItem {
  id: string;
  symbol: string;
  name: string;
  image_url: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  price_change_pct_24h: number;
  total_volume: number;
  binance_symbol: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

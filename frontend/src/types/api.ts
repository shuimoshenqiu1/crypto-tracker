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

export interface CoinDetail {
  id: string;
  symbol: string;
  name: string;
  image_url: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  price_change_24h: number;
  price_change_pct_24h: number;
  total_volume: number;
  circulating_supply: number;
  max_supply: number | null;
  ath: number;
  ath_date: number;
  binance_symbol: string;
  updated_at: number;
}

export interface KlineData {
  open_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  close_time: number;
  quote_volume: number;
  trades_count: number;
}

export interface KlineResponse {
  coin_id: string;
  symbol: string;
  interval: string;
  klines: KlineData[];
}

export interface WatchlistItem {
  coin_id: string;
  symbol: string;
  name: string;
  image_url: string;
  current_price: number;
  price_change_pct_24h: number;
  sort_order: number;
  added_at: number;
}

export interface WatchlistResponse {
  items: WatchlistItem[];
  total: number;
}

export interface WatchlistAddResponse {
  coin_id: string;
  sort_order: number;
  added_at: number;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  price_change_pct_24h: number;
  volume_24h: number;
  timestamp: number;
}

// Alert types
export type ConditionType = 'price_above' | 'price_below' | 'pct_change_above' | 'pct_change_below';

export interface AlertItem {
  id: string;
  coin_id: string;
  coin_symbol: string;
  coin_name: string;
  condition_type: ConditionType;
  threshold: number;
  is_active: boolean;
  is_repeating: boolean;
  cooldown_secs: number;
  last_triggered: number | null;
  created_at: number;
  updated_at: number;
}

export interface AlertHistoryItem {
  id: string;
  alert_id: string;
  coin_id: string;
  coin_symbol: string;
  condition_type: ConditionType;
  threshold: number;
  trigger_price: number;
  message: string;
  triggered_at: number;
}

export interface CreateAlertRequest {
  coin_id: string;
  condition_type: ConditionType;
  threshold: number;
  is_repeating?: boolean;
  cooldown_secs?: number;
}

export interface UpdateAlertRequest {
  threshold?: number;
  is_active?: boolean;
  is_repeating?: boolean;
  cooldown_secs?: number;
}

export interface AlertTriggeredEvent {
  alert_id: string;
  coin_id: string;
  coin_symbol: string;
  condition_type: ConditionType;
  threshold: number;
  trigger_price: number;
  message: string;
  triggered_at: number;
}

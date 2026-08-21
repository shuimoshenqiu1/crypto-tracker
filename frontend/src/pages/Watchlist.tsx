import { useEffect, useState, useCallback, useRef } from 'react';
import { Table, Space, Typography, Tag, Button, Empty, message } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import type { WatchlistItem } from '../types/api';
import { getWatchlist, removeFromWatchlist } from '../services/watchlist';
import { useWebSocket } from '../hooks/useWebSocket';

const { Title } = Typography;

function formatPrice(value: number): string {
  if (value >= 1) {
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `$${value.toPrecision(4)}`;
}

export default function Watchlist() {
  const navigate = useNavigate();
  const [data, setData] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const { prices, subscribe, connected } = useWebSocket();
  const [flashMap, setFlashMap] = useState<Map<string, 'up' | 'down'>>(new Map());
  const flashTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getWatchlist();
      if (res.code === 0) {
        setData(res.data.items);
      }
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Subscribe to WebSocket price updates for watchlist items
  useEffect(() => {
    if (connected && data.length > 0) {
      // We need binance_symbol but WatchlistItem only has symbol (e.g. BTC)
      // Construct from symbol + USDT
      const symbols = data.map((item) => `${item.symbol.toUpperCase()}USDT`);
      subscribe(symbols);
    }
  }, [connected, data, subscribe]);

  // Flash effect on price update
  const prevPrices = useRef<Map<string, number>>(new Map());
  useEffect(() => {
    prices.forEach((update, symbol) => {
      const prevPrice = prevPrices.current.get(symbol);
      if (prevPrice !== undefined && prevPrice !== update.price) {
        const direction = update.price > prevPrice ? 'up' : 'down';
        setFlashMap((prev) => {
          const next = new Map(prev);
          next.set(symbol, direction);
          return next;
        });
        // Clear flash after 300ms
        const existing = flashTimers.current.get(symbol);
        if (existing) clearTimeout(existing);
        const timer = setTimeout(() => {
          setFlashMap((prev) => {
            const next = new Map(prev);
            next.delete(symbol);
            return next;
          });
          flashTimers.current.delete(symbol);
        }, 300);
        flashTimers.current.set(symbol, timer);
      }
      prevPrices.current.set(symbol, update.price);
    });
  }, [prices]);

  // Cleanup flash timers on unmount
  useEffect(() => {
    return () => {
      flashTimers.current.forEach((timer) => clearTimeout(timer));
    };
  }, []);

  const handleRemove = async (coinId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await removeFromWatchlist(coinId);
      if (res.code === 0) {
        message.success('Removed from watchlist');
        setData((prev) => prev.filter((item) => item.coin_id !== coinId));
      }
    } catch {
      message.error('Failed to remove');
    }
  };

  const getDisplayPrice = (item: WatchlistItem): number => {
    const wsSymbol = `${item.symbol.toUpperCase()}USDT`;
    const wsPrice = prices.get(wsSymbol);
    return wsPrice ? wsPrice.price : item.current_price;
  };

  const getDisplayChange = (item: WatchlistItem): number => {
    const wsSymbol = `${item.symbol.toUpperCase()}USDT`;
    const wsPrice = prices.get(wsSymbol);
    return wsPrice ? wsPrice.price_change_pct_24h : item.price_change_pct_24h;
  };

  const getFlashStyle = (item: WatchlistItem): React.CSSProperties => {
    const wsSymbol = `${item.symbol.toUpperCase()}USDT`;
    const flash = flashMap.get(wsSymbol);
    if (!flash) return { transition: 'background-color 0.3s' };
    return {
      transition: 'background-color 0.3s',
      backgroundColor: flash === 'up' ? 'rgba(82, 196, 26, 0.15)' : 'rgba(245, 34, 45, 0.15)',
    };
  };

  const columns: ColumnsType<WatchlistItem> = [
    {
      title: 'Coin',
      key: 'name',
      render: (_: unknown, record: WatchlistItem) => (
        <Space>
          <img
            src={record.image_url}
            alt={record.name}
            style={{ width: 24, height: 24, borderRadius: '50%' }}
          />
          <span style={{ fontWeight: 500 }}>{record.name}</span>
          <Tag>{record.symbol.toUpperCase()}</Tag>
        </Space>
      ),
    },
    {
      title: 'Price',
      key: 'current_price',
      align: 'right',
      render: (_: unknown, record: WatchlistItem) => (
        <span>{formatPrice(getDisplayPrice(record))}</span>
      ),
    },
    {
      title: '24h %',
      key: 'price_change_pct_24h',
      align: 'right',
      render: (_: unknown, record: WatchlistItem) => {
        const value = getDisplayChange(record);
        return (
          <span style={{ color: value >= 0 ? '#52c41a' : '#f5222d', fontWeight: 500 }}>
            {value >= 0 ? '+' : ''}{value.toFixed(2)}%
          </span>
        );
      },
    },
    {
      title: 'Action',
      key: 'action',
      align: 'center',
      width: 80,
      render: (_: unknown, record: WatchlistItem) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={(e) => handleRemove(record.coin_id, e)}
          title="Remove from watchlist"
        />
      ),
    },
  ];

  if (!loading && data.length === 0) {
    return (
      <div>
        <Title level={4} style={{ marginBottom: 16 }}>Watchlist</Title>
        <Empty
          description="Your watchlist is empty"
          style={{ marginTop: 64 }}
        >
          <Button type="primary" onClick={() => navigate('/coins')}>
            Browse Coins
          </Button>
        </Empty>
      </div>
    );
  }

  return (
    <div>
      <Space style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0 }}>Watchlist</Title>
        {connected && <Tag color="green">Live</Tag>}
      </Space>
      <Table<WatchlistItem>
        columns={columns}
        dataSource={data}
        rowKey="coin_id"
        loading={loading}
        pagination={false}
        onRow={(record) => ({
          onClick: () => navigate(`/coins/${record.coin_id}`),
          style: { cursor: 'pointer', ...getFlashStyle(record) },
        })}
      />
    </div>
  );
}

import { useEffect, useState, useCallback, useRef } from 'react';
import { Table, Input, Space, Typography, Tag, message } from 'antd';
import { SearchOutlined, StarOutlined, StarFilled } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import type { SorterResult } from 'antd/es/table/interface';
import type { CoinListItem } from '../types/api';
import { getCoins, type CoinsParams } from '../services/coins';
import { getWatchlist, addToWatchlist, removeFromWatchlist } from '../services/watchlist';

const { Title } = Typography;

function formatLargeNumber(value: number): string {
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(2)}B`;
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }
  return `$${value.toLocaleString()}`;
}

function formatPrice(value: number): string {
  if (value >= 1) {
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `$${value.toPrecision(4)}`;
}

export default function Coins() {
  const navigate = useNavigate();
  const [data, setData] = useState<CoinListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState<CoinsParams>({
    page: 1,
    page_size: 20,
    sort_by: 'market_cap_rank',
    sort_order: 'asc',
  });
  const [searchValue, setSearchValue] = useState('');
  const [watchlistIds, setWatchlistIds] = useState<Set<string>>(new Set());
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const refreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async (fetchParams: CoinsParams) => {
    setLoading(true);
    try {
      const res = await getCoins(fetchParams);
      if (res.code === 0) {
        setData(res.data.items);
        setTotal(res.data.total);
      }
    } catch {
      // Error handled by axios interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchWatchlist = useCallback(async () => {
    try {
      const res = await getWatchlist();
      if (res.code === 0) {
        setWatchlistIds(new Set(res.data.items.map((item) => item.coin_id)));
      }
    } catch {
      // Non-critical, ignore
    }
  }, []);

  useEffect(() => {
    fetchData(params);
  }, [params, fetchData]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    refreshTimer.current = setInterval(() => {
      fetchData(params);
    }, 60000);
    return () => {
      if (refreshTimer.current) clearInterval(refreshTimer.current);
    };
  }, [params, fetchData]);

  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setParams((prev) => ({ ...prev, page: 1, search: value || undefined }));
    }, 500);
  };

  const handleTableChange = (
    pagination: TablePaginationConfig,
    _filters: Record<string, unknown>,
    sorter: SorterResult<CoinListItem> | SorterResult<CoinListItem>[]
  ) => {
    const singleSorter = Array.isArray(sorter) ? sorter[0] : sorter;
    const newParams: CoinsParams = {
      ...params,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 20,
    };
    if (singleSorter.field && singleSorter.order) {
      newParams.sort_by = singleSorter.field as string;
      newParams.sort_order = singleSorter.order === 'ascend' ? 'asc' : 'desc';
    } else {
      newParams.sort_by = 'market_cap_rank';
      newParams.sort_order = 'asc';
    }
    setParams(newParams);
  };

  const handleToggleWatchlist = async (coinId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (togglingIds.has(coinId)) return;

    setTogglingIds((prev) => new Set(prev).add(coinId));
    try {
      if (watchlistIds.has(coinId)) {
        const res = await removeFromWatchlist(coinId);
        if (res.code === 0) {
          setWatchlistIds((prev) => {
            const next = new Set(prev);
            next.delete(coinId);
            return next;
          });
          message.success('Removed from watchlist');
        }
      } else {
        const res = await addToWatchlist(coinId);
        if (res.code === 0) {
          setWatchlistIds((prev) => new Set(prev).add(coinId));
          message.success('Added to watchlist');
        }
      }
    } catch {
      message.error('Operation failed');
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(coinId);
        return next;
      });
    }
  };

  const columns: ColumnsType<CoinListItem> = [
    {
      title: '',
      key: 'watchlist',
      width: 40,
      render: (_: unknown, record: CoinListItem) => {
        const isInWatchlist = watchlistIds.has(record.id);
        return (
          <span
            onClick={(e) => handleToggleWatchlist(record.id, e)}
            style={{ cursor: 'pointer', fontSize: 16 }}
            title={isInWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
          >
            {isInWatchlist ? (
              <StarFilled style={{ color: '#faad14' }} />
            ) : (
              <StarOutlined style={{ color: '#d9d9d9' }} />
            )}
          </span>
        );
      },
    },
    {
      title: '#',
      dataIndex: 'market_cap_rank',
      key: 'market_cap_rank',
      width: 60,
      sorter: true,
    },
    {
      title: 'Coin',
      key: 'name',
      sorter: true,
      render: (_: unknown, record: CoinListItem) => (
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
      dataIndex: 'current_price',
      key: 'current_price',
      align: 'right',
      render: (value: number) => formatPrice(value),
    },
    {
      title: '24h %',
      dataIndex: 'price_change_pct_24h',
      key: 'price_change_pct_24h',
      align: 'right',
      sorter: true,
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#f5222d', fontWeight: 500 }}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: 'Market Cap',
      dataIndex: 'market_cap',
      key: 'market_cap',
      align: 'right',
      render: (value: number) => formatLargeNumber(value),
    },
    {
      title: 'Volume',
      dataIndex: 'total_volume',
      key: 'total_volume',
      align: 'right',
      sorter: true,
      render: (value: number) => formatLargeNumber(value),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0 }}>Market</Title>
        <Input
          placeholder="Search coins..."
          prefix={<SearchOutlined />}
          value={searchValue}
          onChange={(e) => handleSearch(e.target.value)}
          style={{ width: 240 }}
          allowClear
        />
      </Space>
      <Table<CoinListItem>
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          current: params.page,
          pageSize: params.page_size,
          total,
          showSizeChanger: true,
          showTotal: (t) => `Total ${t} coins`,
        }}
        onChange={handleTableChange}
        onRow={(record) => ({
          onClick: () => navigate(`/coins/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
}

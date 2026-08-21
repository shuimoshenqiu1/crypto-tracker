import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Spin, Alert, Button, Card, Statistic, Row, Col, Space } from 'antd';
import { ArrowLeftOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { getCoinDetail } from '../services/coins';
import type { CoinDetail as CoinDetailType } from '../types/api';
import KlineChart from '../components/KlineChart';
import IntervalSelector from '../components/IntervalSelector';

const { Title } = Typography;

export default function CoinDetail() {
  const { coinId } = useParams<{ coinId: string }>();
  const navigate = useNavigate();
  const [coin, setCoin] = useState<CoinDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [interval, setInterval] = useState('1h');

  useEffect(() => {
    if (!coinId) return;
    let cancelled = false;

    async function fetchCoin() {
      setLoading(true);
      setError(null);
      try {
        const res = await getCoinDetail(coinId!);
        if (!cancelled) {
          if (res.code === 0) {
            setCoin(res.data);
          } else {
            setError(res.message || 'Failed to load coin detail');
          }
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : 'Network error';
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchCoin();
    return () => { cancelled = true; };
  }, [coinId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/coins')} style={{ marginBottom: 16 }}>
          Back
        </Button>
        <Alert type="error" message="Error" description={error} showIcon />
      </div>
    );
  }

  if (!coin) return null;

  const isPositive = coin.price_change_pct_24h >= 0;

  return (
    <div style={{ padding: 24 }}>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/coins')} style={{ marginBottom: 16 }}>
        Back to Coins
      </Button>

      <Card style={{ marginBottom: 24 }}>
        <Space align="center" style={{ marginBottom: 16 }}>
          {coin.image_url && (
            <img src={coin.image_url} alt={coin.name} style={{ width: 32, height: 32 }} />
          )}
          <Title level={3} style={{ margin: 0 }}>
            {coin.name} ({coin.symbol.toUpperCase()})
          </Title>
        </Space>

        <Row gutter={[24, 16]}>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="Current Price"
              value={coin.current_price}
              precision={2}
              prefix="$"
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="24h Change"
              value={coin.price_change_pct_24h}
              precision={2}
              suffix="%"
              valueStyle={{ color: isPositive ? '#3f8600' : '#cf1322' }}
              prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="Market Cap"
              value={coin.market_cap}
              precision={0}
              prefix="$"
            />
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Statistic
              title="24h Volume"
              value={coin.total_volume}
              precision={0}
              prefix="$"
            />
          </Col>
        </Row>
      </Card>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <IntervalSelector value={interval} onChange={setInterval} />
        </div>
        {coinId && <KlineChart coinId={coinId} interval={interval} />}
      </Card>
    </div>
  );
}

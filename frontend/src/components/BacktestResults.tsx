import { useEffect, useRef } from 'react';
import { Card, Row, Col, Statistic, Table, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { createChart, ColorType } from 'lightweight-charts';
import type { BacktestResult } from '../types/api';

const { Title } = Typography;

interface BacktestResultsProps {
  result: BacktestResult;
}

export default function BacktestResults({ result }: BacktestResultsProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current || result.equity_curve.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: 300,
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const lineSeries = chart.addLineSeries({
      color: result.total_return_pct >= 0 ? '#52c41a' : '#ff4d4f',
      lineWidth: 2,
    });

    const lineData = result.equity_curve.map((point) => ({
      time: Math.floor(point.time / 1000) as unknown as import('lightweight-charts').UTCTimestamp,
      value: point.value,
    }));

    lineSeries.setData(lineData);
    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [result]);

  const tradeColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <span style={{ color: type === 'buy' ? '#52c41a' : '#ff4d4f', fontWeight: 600 }}>
          {type.toUpperCase()}
        </span>
      ),
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    },
    {
      title: 'Time',
      dataIndex: 'time',
      key: 'time',
      render: (time: number) => new Date(time).toLocaleString(),
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (qty: number) => qty.toFixed(4),
    },
  ];

  // Pair trades to compute P&L per round-trip
  const pairedTrades = [];
  for (let i = 0; i < result.trades.length - 1; i += 2) {
    const buy = result.trades[i];
    const sell = result.trades[i + 1];
    if (buy && sell && buy.type === 'buy' && sell.type === 'sell') {
      const pnl = (sell.price - buy.price) * buy.quantity;
      const pnlPct = ((sell.price - buy.price) / buy.price) * 100;
      pairedTrades.push({
        key: i,
        entry_time: buy.time,
        exit_time: sell.time,
        entry_price: buy.price,
        exit_price: sell.price,
        pnl,
        pnl_pct: pnlPct,
      });
    }
  }

  const pairedColumns = [
    {
      title: 'Entry Time',
      dataIndex: 'entry_time',
      key: 'entry_time',
      render: (t: number) => new Date(t).toLocaleString(),
    },
    {
      title: 'Entry Price',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (p: number) => `$${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    },
    {
      title: 'Exit Time',
      dataIndex: 'exit_time',
      key: 'exit_time',
      render: (t: number) => new Date(t).toLocaleString(),
    },
    {
      title: 'Exit Price',
      dataIndex: 'exit_price',
      key: 'exit_price',
      render: (p: number) => `$${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    },
    {
      title: 'P&L',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span style={{ color: pnl >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
        </span>
      ),
    },
    {
      title: 'P&L %',
      dataIndex: 'pnl_pct',
      key: 'pnl_pct',
      render: (pct: number) => (
        <span style={{ color: pct >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
        </span>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginTop: 24 }}>Backtest Results</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="Total Return"
              value={result.total_return_pct}
              precision={2}
              suffix="%"
              valueStyle={{ color: result.total_return_pct >= 0 ? '#52c41a' : '#ff4d4f' }}
              prefix={result.total_return_pct >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="Win Rate"
              value={result.win_rate_pct}
              precision={2}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="Max Drawdown"
              value={result.max_drawdown_pct}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="Sharpe Ratio"
              value={result.sharpe_ratio}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="Total Trades"
              value={result.total_trades}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="Profit Factor"
              value={result.profit_factor}
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Equity Curve" style={{ marginBottom: 24 }}>
        <div ref={chartContainerRef} />
      </Card>

      {pairedTrades.length > 0 ? (
        <Card title="Trades (Round-trips)">
          <Table
            dataSource={pairedTrades}
            columns={pairedColumns}
            size="small"
            pagination={{ pageSize: 10 }}
          />
        </Card>
      ) : (
        <Card title="Trades">
          <Table
            dataSource={result.trades.map((t, i) => ({ ...t, key: i }))}
            columns={tradeColumns}
            size="small"
            pagination={{ pageSize: 10 }}
          />
        </Card>
      )}
    </div>
  );
}

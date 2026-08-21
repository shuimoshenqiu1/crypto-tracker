import { useState, useEffect, useCallback } from 'react';
import {
  Card, Form, Select, Radio, InputNumber, DatePicker, Button, Space,
  Spin, Alert, Typography, Row, Col,
} from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { getCoins } from '../services/coins';
import { submitBacktest, getBacktestResult, getStrategies } from '../services/backtest';
import BacktestResults from '../components/BacktestResults';
import type { CoinListItem, StrategyInfo, BacktestJob, StrategyName } from '../types/api';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const INTERVALS = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1d', value: '1d' },
];

export default function Backtest() {
  const [form] = Form.useForm();
  const [coins, setCoins] = useState<CoinListItem[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyName | null>(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [jobResult, setJobResult] = useState<BacktestJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [coinSearch, setCoinSearch] = useState('');

  useEffect(() => {
    loadStrategies();
    loadCoins('');
  }, []);

  const loadStrategies = async () => {
    try {
      const res = await getStrategies();
      if (res.code === 0) {
        setStrategies(res.data.strategies);
        if (res.data.strategies.length > 0) {
          const first = res.data.strategies[0];
          setSelectedStrategy(first.name);
          form.setFieldsValue({ strategy_name: first.name });
        }
      }
    } catch {
      // strategies will use hardcoded fallback below
    }
  };

  const loadCoins = async (search: string) => {
    try {
      const res = await getCoins({ page: 1, page_size: 50, search });
      if (res.code === 0) {
        setCoins(res.data.items);
      }
    } catch {
      // ignore
    }
  };

  const handleCoinSearch = (value: string) => {
    setCoinSearch(value);
    loadCoins(value);
  };

  const currentStrategy = strategies.find((s) => s.name === selectedStrategy) || null;

  const pollJob = useCallback(async (jobId: string) => {
    setPolling(true);
    setError(null);
    const poll = async () => {
      try {
        const res = await getBacktestResult(jobId);
        if (res.code === 0) {
          const job = res.data;
          if (job.status === 'completed' || job.status === 'failed') {
            setJobResult(job);
            setPolling(false);
            if (job.status === 'failed') {
              setError(job.error_message || 'Backtest failed');
            }
            return;
          }
          // Still running, poll again
          setTimeout(poll, 2000);
        } else {
          setError('Failed to fetch job status');
          setPolling(false);
        }
      } catch {
        setError('Network error while polling');
        setPolling(false);
      }
    };
    poll();
  }, []);

  const handleSubmit = async (values: {
    coin_id: string;
    strategy_name: StrategyName;
    interval: string;
    date_range: [Dayjs, Dayjs];
    [key: string]: unknown;
  }) => {
    setLoading(true);
    setError(null);
    setJobResult(null);

    // Extract strategy params
    const params: Record<string, number> = {};
    if (currentStrategy) {
      for (const key of Object.keys(currentStrategy.params_schema)) {
        const val = values[key];
        if (val !== undefined && val !== null) {
          params[key] = Number(val);
        }
      }
    }

    const [startDate, endDate] = values.date_range;

    try {
      const res = await submitBacktest({
        coin_id: values.coin_id,
        strategy_name: values.strategy_name,
        params,
        interval: values.interval,
        start_time: startDate.valueOf(),
        end_time: endDate.valueOf(),
      });

      if (res.code === 0) {
        pollJob(res.data.job_id);
      } else {
        setError(res.message || 'Failed to submit backtest');
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Submit failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Default date range: last 30 days
  const defaultRange: [Dayjs, Dayjs] = [dayjs().subtract(30, 'day'), dayjs()];

  return (
    <div>
      <Title level={3}><ExperimentOutlined /> Backtest</Title>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            interval: '1h',
            date_range: defaultRange,
          }}
        >
          {/* Strategy Selector */}
          <Form.Item
            label="Strategy"
            name="strategy_name"
            rules={[{ required: true, message: 'Select a strategy' }]}
          >
            <Radio.Group
              onChange={(e) => setSelectedStrategy(e.target.value)}
              optionType="button"
              buttonStyle="solid"
            >
              {strategies.map((s) => (
                <Radio.Button key={s.name} value={s.name}>
                  {s.display_name}
                </Radio.Button>
              ))}
            </Radio.Group>
          </Form.Item>

          {currentStrategy && (
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              {currentStrategy.description}
            </Text>
          )}

          {/* Dynamic Strategy Params */}
          {currentStrategy && (
            <Card size="small" title="Strategy Parameters" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                {Object.entries(currentStrategy.params_schema).map(([key, schema]) => (
                  <Col span={8} key={key}>
                    <Form.Item
                      label={schema.description}
                      name={key}
                      initialValue={schema.default}
                      rules={[
                        { required: true, message: `Required` },
                        {
                          type: 'number',
                          min: schema.min,
                          max: schema.max,
                          message: `${schema.min} - ${schema.max}`,
                        },
                      ]}
                    >
                      <InputNumber
                        min={schema.min}
                        max={schema.max}
                        step={schema.type === 'float' ? 0.1 : 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Col>
                ))}
              </Row>
            </Card>
          )}

          {/* Coin Selector */}
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Coin"
                name="coin_id"
                rules={[{ required: true, message: 'Select a coin' }]}
              >
                <Select
                  showSearch
                  placeholder="Search coin..."
                  filterOption={false}
                  onSearch={handleCoinSearch}
                  searchValue={coinSearch}
                  options={coins.map((c) => ({
                    label: `${c.name} (${c.symbol})`,
                    value: c.id,
                  }))}
                />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item
                label="Interval"
                name="interval"
                rules={[{ required: true }]}
              >
                <Select options={INTERVALS} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Date Range"
                name="date_range"
                rules={[{ required: true, message: 'Select date range' }]}
              >
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                disabled={polling}
                icon={<ExperimentOutlined />}
              >
                Run Backtest
              </Button>
              {polling && <Spin tip="Running backtest..." />}
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {error && (
        <Alert
          type="error"
          message="Backtest Error"
          description={error}
          showIcon
          style={{ marginTop: 16 }}
        />
      )}

      {jobResult?.status === 'completed' && jobResult.result && (
        <BacktestResults result={jobResult.result} />
      )}
    </div>
  );
}

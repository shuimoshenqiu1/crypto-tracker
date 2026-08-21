import { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Select,
  InputNumber,
  Switch,
  Tabs,
  Tag,
  Popconfirm,
  message,
  Typography,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type {
  AlertItem,
  AlertHistoryItem,
  CreateAlertRequest,
  UpdateAlertRequest,
  CoinListItem,
  PaginatedResponse,
  ConditionType,
} from '../types/api';
import { getAlerts, createAlert, updateAlert, deleteAlert, getAlertHistory } from '../services/alerts';
import { getCoins } from '../services/coins';

const { Title } = Typography;

const CONDITION_LABELS: Record<ConditionType, string> = {
  price_above: '价格高于',
  price_below: '价格低于',
  pct_change_above: '涨幅超过',
  pct_change_below: '跌幅超过',
};

function isPriceCondition(type: ConditionType): boolean {
  return type === 'price_above' || type === 'price_below';
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<PaginatedResponse<AlertItem>>({ items: [], total: 0, page: 1, page_size: 20 });
  const [history, setHistory] = useState<PaginatedResponse<AlertHistoryItem>>({ items: [], total: 0, page: 1, page_size: 20 });
  const [coins, setCoins] = useState<CoinListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAlert, setEditingAlert] = useState<AlertItem | null>(null);
  const [form] = Form.useForm();
  const [conditionType, setConditionType] = useState<ConditionType>('price_above');

  const fetchAlerts = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const data = await getAlerts({ page, page_size: 20 });
      setAlerts(data);
    } catch {
      message.error('获取告警列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async (page = 1) => {
    setHistoryLoading(true);
    try {
      const data = await getAlertHistory({ page, page_size: 20 });
      setHistory(data);
    } catch {
      message.error('获取告警历史失败');
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const fetchCoins = useCallback(async () => {
    try {
      const res = await getCoins({ page: 1, page_size: 100 });
      setCoins(res.data.items);
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    fetchHistory();
    fetchCoins();
  }, [fetchAlerts, fetchHistory, fetchCoins]);

  const handleCreate = () => {
    setEditingAlert(null);
    form.resetFields();
    setConditionType('price_above');
    setModalVisible(true);
  };

  const handleEdit = (record: AlertItem) => {
    setEditingAlert(record);
    setConditionType(record.condition_type);
    form.setFieldsValue({
      coin_id: record.coin_id,
      condition_type: record.condition_type,
      threshold: record.threshold,
      is_repeating: record.is_repeating,
      cooldown_secs: record.cooldown_secs,
    });
    setModalVisible(true);
  };

  const handleDelete = async (alertId: string) => {
    try {
      await deleteAlert(alertId);
      message.success('删除成功');
      fetchAlerts(alerts.page);
    } catch {
      message.error('删除失败');
    }
  };

  const handleToggleActive = async (record: AlertItem) => {
    try {
      await updateAlert(record.id, { is_active: !record.is_active });
      message.success(record.is_active ? '已静默' : '已激活');
      fetchAlerts(alerts.page);
    } catch {
      message.error('操作失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingAlert) {
        const updateData: UpdateAlertRequest = {
          threshold: values.threshold,
          is_repeating: values.is_repeating,
          cooldown_secs: values.cooldown_secs,
        };
        await updateAlert(editingAlert.id, updateData);
        message.success('更新成功');
      } else {
        const createData: CreateAlertRequest = {
          coin_id: values.coin_id,
          condition_type: values.condition_type,
          threshold: values.threshold,
          is_repeating: values.is_repeating,
          cooldown_secs: values.cooldown_secs,
        };
        await createAlert(createData);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchAlerts(alerts.page);
    } catch {
      // form validation error or api error
    }
  };

  const alertColumns: ColumnsType<AlertItem> = [
    {
      title: '币种',
      dataIndex: 'coin_symbol',
      key: 'coin_symbol',
      render: (symbol: string, record: AlertItem) => `${record.coin_name} (${symbol})`,
    },
    {
      title: '条件',
      dataIndex: 'condition_type',
      key: 'condition_type',
      render: (type: ConditionType) => CONDITION_LABELS[type],
    },
    {
      title: '阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (threshold: number, record: AlertItem) =>
        isPriceCondition(record.condition_type) ? `$${threshold.toLocaleString()}` : `${threshold}%`,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean, record: AlertItem) => (
        <Switch
          checked={active}
          onChange={() => handleToggleActive(record)}
          checkedChildren="激活"
          unCheckedChildren="静默"
        />
      ),
    },
    {
      title: '重复',
      dataIndex: 'is_repeating',
      key: 'is_repeating',
      render: (repeating: boolean) => (
        <Tag color={repeating ? 'blue' : 'default'}>{repeating ? '重复' : '一次'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: AlertItem) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除此告警规则吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const historyColumns: ColumnsType<AlertHistoryItem> = [
    {
      title: '币种',
      dataIndex: 'coin_symbol',
      key: 'coin_symbol',
    },
    {
      title: '条件',
      dataIndex: 'condition_type',
      key: 'condition_type',
      render: (type: ConditionType) => CONDITION_LABELS[type],
    },
    {
      title: '阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (threshold: number, record: AlertHistoryItem) =>
        isPriceCondition(record.condition_type) ? `$${threshold.toLocaleString()}` : `${threshold}%`,
    },
    {
      title: '触发价格',
      dataIndex: 'trigger_price',
      key: 'trigger_price',
      render: (price: number) => `$${price.toLocaleString()}`,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: '触发时间',
      dataIndex: 'triggered_at',
      key: 'triggered_at',
      render: (ts: number) => new Date(ts).toLocaleString(),
    },
  ];

  const tabItems = [
    {
      key: 'active',
      label: '活跃告警',
      children: (
        <>
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              创建告警
            </Button>
          </div>
          <Table<AlertItem>
            rowKey="id"
            columns={alertColumns}
            dataSource={alerts.items}
            loading={loading}
            pagination={{
              current: alerts.page,
              pageSize: alerts.page_size,
              total: alerts.total,
              onChange: (page) => fetchAlerts(page),
            }}
          />
        </>
      ),
    },
    {
      key: 'history',
      label: '触发历史',
      children: (
        <Table<AlertHistoryItem>
          rowKey="id"
          columns={historyColumns}
          dataSource={history.items}
          loading={historyLoading}
          pagination={{
            current: history.page,
            pageSize: history.page_size,
            total: history.total,
            onChange: (page) => fetchHistory(page),
          }}
        />
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>告警管理</Title>
      <Tabs items={tabItems} />

      <Modal
        title={editingAlert ? '编辑告警' : '创建告警'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" initialValues={{ is_repeating: false, cooldown_secs: 3600 }}>
          {!editingAlert && (
            <Form.Item
              name="coin_id"
              label="选择币种"
              rules={[{ required: true, message: '请选择币种' }]}
            >
              <Select
                showSearch
                placeholder="搜索并选择币种"
                optionFilterProp="label"
                options={coins.map((c) => ({
                  value: c.id,
                  label: `${c.name} (${c.symbol})`,
                }))}
              />
            </Form.Item>
          )}
          {!editingAlert && (
            <Form.Item
              name="condition_type"
              label="告警条件"
              rules={[{ required: true, message: '请选择条件' }]}
            >
              <Select
                onChange={(value: ConditionType) => setConditionType(value)}
                options={Object.entries(CONDITION_LABELS).map(([value, label]) => ({
                  value,
                  label,
                }))}
              />
            </Form.Item>
          )}
          <Form.Item
            name="threshold"
            label={`阈值 (${isPriceCondition(conditionType) ? 'USD' : '%'})`}
            rules={[
              { required: true, message: '请输入阈值' },
              { type: 'number', min: 0.000001, message: '阈值必须大于0' },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              prefix={isPriceCondition(conditionType) ? '$' : undefined}
              suffix={!isPriceCondition(conditionType) ? '%' : undefined}
              placeholder={isPriceCondition(conditionType) ? '如: 70000' : '如: 5.0'}
            />
          </Form.Item>
          <Form.Item name="is_repeating" label="重复触发" valuePropName="checked">
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
          <Form.Item name="cooldown_secs" label="冷却时间(秒)">
            <InputNumber style={{ width: '100%' }} min={60} placeholder="默认 3600" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

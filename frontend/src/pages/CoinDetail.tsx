import { useParams } from 'react-router-dom';
import { Typography } from 'antd';

const { Title, Text } = Typography;

export default function CoinDetail() {
  const { coinId } = useParams<{ coinId: string }>();

  return (
    <div>
      <Title level={4}>Coin Detail</Title>
      <Text>Coin ID: <strong>{coinId}</strong></Text>
      <br />
      <Text type="secondary">详细信息将在 Stage 3 实现</Text>
    </div>
  );
}

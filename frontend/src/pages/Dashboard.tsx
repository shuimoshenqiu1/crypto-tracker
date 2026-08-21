import { Typography, Card } from 'antd';
import { useAuthStore } from '../stores/authStore';

const { Title, Text } = Typography;

export default function Dashboard() {
  const { user } = useAuthStore();

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Card>
        <Title level={3}>
          Welcome, {user?.username || 'User'}
        </Title>
        <Text type="secondary">
          Your crypto portfolio dashboard will appear here.
        </Text>
      </Card>
    </div>
  );
}

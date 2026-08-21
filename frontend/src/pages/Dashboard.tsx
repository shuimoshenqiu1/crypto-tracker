import { Typography } from 'antd';
import { useAuthStore } from '../stores/authStore';

const { Title } = Typography;

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);

  return (
    <div>
      <Title level={2}>Welcome, {user?.name}</Title>
    </div>
  );
}

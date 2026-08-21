import { Layout as AntLayout, Button, Typography } from 'antd';
import { LogoutOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import { useNavigate, Outlet } from 'react-router-dom';

const { Header, Content } = AntLayout;
const { Title } = Typography;

export default function Layout() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={4} style={{ color: '#fff', margin: 0 }}>
          🪙 CryptoTracker
        </Title>
        <Button
          type="text"
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          style={{ color: '#fff' }}
        >
          Logout
        </Button>
      </Header>
      <Content style={{ padding: '24px 48px' }}>
        <Outlet />
      </Content>
    </AntLayout>
  );
}

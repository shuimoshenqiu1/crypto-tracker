import { Layout, Button, Space, Typography, Menu } from 'antd';
import { LogoutOutlined, DashboardOutlined, LineChartOutlined, StarOutlined, BellOutlined, ExperimentOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useAlertWebSocket } from '../hooks/useAlertWebSocket';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/coins', icon: <LineChartOutlined />, label: 'Market' },
  { key: '/watchlist', icon: <StarOutlined />, label: 'Watchlist' },
  { key: '/alerts', icon: <BellOutlined />, label: 'Alerts' },
  { key: '/backtest', icon: <ExperimentOutlined />, label: 'Backtest' },
];

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // Start alert WebSocket for real-time notifications on all pages
  useAlertWebSocket();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getSelectedKey = () => {
    if (location.pathname.startsWith('/coins')) return '/coins';
    if (location.pathname.startsWith('/watchlist')) return '/watchlist';
    if (location.pathname.startsWith('/alerts')) return '/alerts';
    if (location.pathname.startsWith('/backtest')) return '/backtest';
    return '/';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={4} style={{ color: '#fff', margin: 0 }}>
          CryptoTracker
        </Title>
        <Space>
          <span style={{ color: '#fff' }}>{user?.name}</span>
          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            style={{ color: '#fff' }}
          >
            退出
          </Button>
        </Space>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[getSelectedKey()]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Content style={{ padding: '24px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

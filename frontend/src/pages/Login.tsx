import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { MailOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { AxiosError } from 'axios';
import { ApiResponse } from '../types/api';

const { Title, Text } = Typography;

interface LoginForm {
  email: string;
  password: string;
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuthStore();
  const [form] = Form.useForm<LoginForm>();

  // Show success message if redirected from register
  const searchParams = new URLSearchParams(location.search);
  const registered = searchParams.get('registered');

  const onFinish = async (values: LoginForm) => {
    try {
      await login(values.email, values.password);
      message.success('Login successful');
      navigate('/', { replace: true });
    } catch (err) {
      const error = err as AxiosError<ApiResponse<null>>;
      const msg = error.response?.data?.message || 'Login failed';
      message.error(msg);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#f0f2f5',
    }}>
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 4 }}>🪙 CryptoTracker</Title>
            <Text type="secondary">Sign in to your account</Text>
          </div>

          {registered && (
            <Text type="success" style={{ display: 'block', textAlign: 'center' }}>
              Registration successful! Please log in.
            </Text>
          )}

          <Form
            form={form}
            layout="vertical"
            onFinish={onFinish}
            autoComplete="off"
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please enter your email' },
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="Email"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: 'Please enter your password' },
                { min: 8, message: 'Password must be at least 8 characters' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Password"
                size="large"
              />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" block size="large">
                Log In
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center' }}>
            <Text>Don&apos;t have an account? </Text>
            <Link to="/register">Register now</Link>
          </div>
        </Space>
      </Card>
    </div>
  );
}

import { Form, Input, Button, Card, Typography, message } from 'antd';
import { MailOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../services/auth';
import { useAuthStore } from '../stores/authStore';
import { AxiosError } from 'axios';
import type { ApiResponse } from '../types/api';

const { Title } = Typography;

interface LoginForm {
  email: string;
  password: string;
}

export default function Login() {
  const navigate = useNavigate();
  const authLogin = useAuthStore((s) => s.login);

  const onFinish = async (values: LoginForm) => {
    try {
      const res = await login(values.email, values.password);
      if (res.code === 0) {
        authLogin(res.data.access_token, res.data.user);
        navigate('/');
      } else {
        message.error(res.message || '登录失败');
      }
    } catch (err) {
      const error = err as AxiosError<ApiResponse<null>>;
      const msg = error.response?.data?.message || '登录失败，请重试';
      message.error(msg);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center' }}>登录</Title>
        <Form<LoginForm> onFinish={onFinish} autoComplete="off" layout="vertical">
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" size="large" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              登录
            </Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            还没有账号？ <Link to="/register">注册</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}

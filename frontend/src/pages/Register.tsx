import { Form, Input, Button, Card, Typography, message } from 'antd';
import { MailOutlined, LockOutlined, UserOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../services/auth';
import { AxiosError } from 'axios';
import type { ApiResponse } from '../types/api';

const { Title } = Typography;

interface RegisterForm {
  email: string;
  password: string;
  name: string;
}

export default function Register() {
  const navigate = useNavigate();

  const onFinish = async (values: RegisterForm) => {
    try {
      const res = await register(values.email, values.password, values.name);
      if (res.code === 0) {
        message.success('注册成功，请登录');
        navigate('/login');
      } else {
        message.error(res.message || '注册失败');
      }
    } catch (err) {
      const error = err as AxiosError<ApiResponse<null>>;
      const code = error.response?.data?.code;
      if (code === 40901) {
        message.error('邮箱已被注册');
      } else {
        const msg = error.response?.data?.message || '注册失败，请重试';
        message.error(msg);
      }
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center' }}>注册</Title>
        <Form<RegisterForm> onFinish={onFinish} autoComplete="off" layout="vertical">
          <Form.Item
            name="name"
            rules={[{ required: true, message: '请输入昵称' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="昵称" size="large" />
          </Form.Item>
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
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '密码至少8位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少8位，含大写和数字）" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              注册
            </Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            已有账号？ <Link to="/login">登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}

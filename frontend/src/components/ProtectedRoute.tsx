import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '../stores/authStore';
import { getMe } from '../services/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { token, logout, setUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [valid, setValid] = useState(false);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    getMe()
      .then((res) => {
        if (res.code === 0) {
          setUser(res.data);
          setValid(true);
        } else {
          logout();
        }
      })
      .catch(() => {
        logout();
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token, logout, setUser]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!token || !valid) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

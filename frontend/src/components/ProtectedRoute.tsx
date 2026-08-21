import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Spin } from 'antd';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, token, loading, checkAuth } = useAuthStore();

  useEffect(() => {
    if (token && !user) {
      checkAuth();
    }
  }, [token, user, checkAuth]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (loading || (!user && token)) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return <>{children}</>;
}

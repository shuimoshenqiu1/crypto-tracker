import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Coins from './pages/Coins';
import CoinDetail from './pages/CoinDetail';
import Watchlist from './pages/Watchlist';
import Alerts from './pages/Alerts';
import Backtest from './pages/Backtest';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="coins" element={<Coins />} />
          <Route path="coins/:coinId" element={<CoinDetail />} />
          <Route path="watchlist" element={<Watchlist />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="backtest" element={<Backtest />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

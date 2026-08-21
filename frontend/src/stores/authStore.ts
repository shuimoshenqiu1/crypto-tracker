import { create } from 'zustand';
import { User } from '../types/user';
import { login as loginApi, getMe } from '../services/auth';
import { getToken, setToken, removeToken } from '../utils/token';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getToken(),
  loading: false,

  login: async (email: string, password: string) => {
    const response = await loginApi({ email, password });
    const { access_token } = response.data;
    setToken(access_token);
    set({ token: access_token });

    // Fetch user info after login
    const meResponse = await getMe();
    set({ user: meResponse.data });
  },

  logout: () => {
    removeToken();
    set({ user: null, token: null });
  },

  checkAuth: async () => {
    const token = getToken();
    if (!token) {
      set({ user: null, token: null, loading: false });
      return;
    }
    try {
      set({ loading: true });
      const response = await getMe();
      set({ user: response.data, token, loading: false });
    } catch {
      removeToken();
      set({ user: null, token: null, loading: false });
    }
  },
}));

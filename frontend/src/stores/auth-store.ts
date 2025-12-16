import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import Cookies from 'js-cookie';
import { authAPI, type User } from '@/lib/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    password: string;
    password2: string;
    role: string;
    phone?: string;
  }) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const response = await authAPI.login(email, password);
          // La réponse peut avoir tokens.access/refresh ou access/refresh directement
          const tokens = response.data.tokens || response.data;
          const access = tokens.access;
          const refresh = tokens.refresh;
          const user = response.data.user || response.data;
          
          if (access) Cookies.set('access_token', access, { expires: 1 });
          if (refresh) Cookies.set('refresh_token', refresh, { expires: 7 });
          
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true });
        try {
          const response = await authAPI.register(data);
          // La réponse peut avoir tokens.access/refresh ou access/refresh directement
          const tokens = response.data.tokens || response.data;
          const access = tokens.access;
          const refresh = tokens.refresh;
          const user = response.data.user || response.data;
          
          if (access) Cookies.set('access_token', access, { expires: 1 });
          if (refresh) Cookies.set('refresh_token', refresh, { expires: 7 });
          
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');
        set({ user: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        const token = Cookies.get('access_token');
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }

        set({ isLoading: true });
        try {
          const response = await authAPI.me();
          set({ user: response.data, isAuthenticated: true, isLoading: false });
        } catch (error) {
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      updateUser: async (data) => {
        const response = await authAPI.updateProfile(data);
        set({ user: response.data });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

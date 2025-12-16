import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs et le refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = Cookies.get('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          Cookies.set('access_token', access, { expires: 1 });
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh token invalide, déconnexion
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  phone: string;
  role: 'buyer' | 'seller' | 'professional';
  avatar: string | null;
  bio: string;
  location: string;
  subscription_type: 'free' | 'basic' | 'pro';
  is_verified: boolean;
  is_active_seller: boolean;
  is_superuser?: boolean;
  avg_rating: number;
  total_reviews: number;
  created_at: string;
}

export interface Listing {
  id: string;
  title: string;
  slug: string;
  description: string;
  price: number;
  original_price?: number;
  category: Category;
  listing_type: 'product' | 'service' | 'rental';
  condition: 'new' | 'like_new' | 'good' | 'fair' | 'poor';
  location: string;
  latitude?: number;
  longitude?: number;
  status: 'draft' | 'pending' | 'active' | 'published' | 'sold' | 'archived';
  is_boosted: boolean;
  boost_expires_at?: string;
  views_count: number;
  favorites_count: number;
  seller: User;
  images: ListingImage[];
  created_at: string;
  updated_at: string;
}

export interface ListingImage {
  id: string;
  image: string;
  is_primary: boolean;
  order: number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon?: string;
  parent?: Category;
  children?: Category[];
}

export interface Message {
  id: string;
  conversation: string;
  sender: User;
  content: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  listing?: string;
  listing_info?: {
    id: string;
    title: string;
    slug: string;
  };
  buyer: User;
  seller: User;
  last_message?: Message;
  unread_count: number;
  last_message_date?: string;
  created_at: string;
}

export interface Review {
  id: string;
  reviewer: User;
  reviewed: User;
  listing?: Listing;
  rating: number;
  comment: string;
  seller_response?: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login/', { email, password }),
  
  register: (data: {
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    password: string;
    password2: string;
    role: string;
    phone?: string;
  }) => api.post('/auth/register/', data),
  
  logout: () => api.post('/auth/logout/'),
  
  me: () => api.get<User>('/auth/me/'),
  
  updateProfile: (data: Partial<User>) => api.put('/auth/me/', data),
  
  changePassword: (data: {
    old_password: string;
    new_password: string;
  }) => api.post('/users/change_password/', data),
  
  resetPassword: (email: string) =>
    api.post('/auth/password-reset/', { email }),
  
  resetPasswordConfirm: (data: { token: string; new_password: string }) =>
    api.post('/auth/password-reset/confirm/', data),
  
  verifyEmail: (token: string) =>
    api.post('/auth/verify-email/', { token }),
  
  resendVerification: (email: string) =>
    api.post('/auth/resend-verification/', { email }),
};

// Listings API
export const listingsAPI = {
  getAll: (params?: Record<string, any>) =>
    api.get<PaginatedResponse<Listing>>('/listings/', { params }),
  
  getOne: (id: string) => api.get<Listing>(`/listings/${id}/`),
  
  // Récupérer par slug (pour les pages de détail)
  getBySlug: (slug: string) => api.get<Listing>(`/listings/by-slug/${slug}/`),
  
  create: (data: FormData) =>
    api.post<Listing>('/listings/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  update: (id: string, data: FormData) =>
    api.patch<Listing>(`/listings/${id}/`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  delete: (id: string) => api.delete(`/listings/${id}/`),
  
  search: (query: string, params?: Record<string, any>) =>
    api.get<PaginatedResponse<Listing>>('/listings/', {
      params: { search: query, ...params },
    }),
  
  getMyListings: () =>
    api.get<PaginatedResponse<Listing>>('/listings/my-listings/'),
  
  canPublish: () =>
    api.get<{
      can_publish: boolean;
      reason: string | null;
      message: string | null;
      has_subscription: boolean;
      has_credits: boolean;
      credits_balance: number;
      subscription_info: {
        plan_name?: string;
        remaining_listings?: number;
        can_create?: boolean;
      };
    }>('/listings/can_publish/'),
  
  getFavorites: () =>
    api.get<PaginatedResponse<Listing>>('/listings/favorites/'),
  
  toggleFavorite: (id: string) =>
    api.post(`/listings/${id}/toggle_favorite/`),
  
  boost: (id: string, days: number) =>
    api.post(`/listings/${id}/boost/`, { days }),
};

// Categories API
export const categoriesAPI = {
  getAll: () => api.get<Category[]>('/listings/categories/'),
  getOne: (slug: string) => api.get<Category>(`/listings/categories/${slug}/`),
};

// Messages API
export const messagesAPI = {
  getConversations: () =>
    api.get<PaginatedResponse<Conversation>>('/messages/conversations/'),
  
  getConversation: (id: string) =>
    api.get<Conversation>(`/messages/conversations/${id}/`),
  
  getMessages: (conversationId: string) =>
    api.get<PaginatedResponse<Message>>(`/messages/conversations/${conversationId}/messages/`),
  
  sendMessage: (conversationId: string, content: string) =>
    api.post<Message>(`/messages/conversations/${conversationId}/send_message/`, {
      content,
    }),
  
  startConversation: (sellerId: string, listingId?: string, content?: string) =>
    api.post<Conversation>('/messages/conversations/start_conversation/', {
      seller_id: sellerId,
      listing_id: listingId,
      content,
    }),
  
  markAsRead: (conversationId: string) =>
    api.post(`/messages/conversations/${conversationId}/mark_read/`),
};

// Reviews API
export const reviewsAPI = {
  getForUser: (userId: string) =>
    api.get<{ reviews: Review[]; count: number; average_rating: number }>(`/reviews/reviews/seller_reviews/?seller_id=${userId}`),
  
  create: (data: {
    seller_id: string;
    listing_id?: string;
    rating: number;
    comment: string;
  }) => api.post<Review>('/reviews/reviews/', data),
  
  respond: (reviewId: string, response: string) =>
    api.post(`/reviews/reviews/${reviewId}/add_response/`, { response }),
};

// Payments API
export const paymentsAPI = {
  createSubscriptionSession: (planId: number, couponCode?: string) =>
    api.post<{ checkout_url: string; session_id: string }>('/payments/create-subscription-session/', { 
      plan_id: planId,
      coupon_code: couponCode,
      success_url: `${typeof window !== 'undefined' ? window.location.origin : ''}/paiement-succes?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${typeof window !== 'undefined' ? window.location.origin : ''}/paiement-annule`,
    }),
  
  createCreditSession: (packId: number, couponCode?: string) =>
    api.post<{ checkout_url: string; session_id: string }>('/payments/create-post-session/', {
      pack_id: packId,
      coupon_code: couponCode,
      success_url: `${typeof window !== 'undefined' ? window.location.origin : ''}/paiement-succes?session_id={CHECKOUT_SESSION_ID}&type=credits`,
      cancel_url: `${typeof window !== 'undefined' ? window.location.origin : ''}/paiement-annule`,
    }),
  
  // Achat d'un article par un acheteur
  createPurchaseSession: (listingId: string) =>
    api.post<{ checkout_url: string; session_id: string }>('/payments/create-purchase-session/', {
      listing_id: listingId,
      success_url: `${typeof window !== 'undefined' ? window.location.origin : ''}/achat-succes?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${typeof window !== 'undefined' ? window.location.origin : ''}/paiement-annule`,
    }),
  
  createBoostSession: (listingId: string, days: number) =>
    api.post('/payments/create-boost-session/', {
      listing_id: listingId,
      days,
    }),
  
  getPaymentHistory: () =>
    api.get('/payments/history/'),
  
  getSubscription: () =>
    api.get('/payments/my-subscription/'),
  
  getCredits: () =>
    api.get<{ balance: number; transactions: any[] }>('/payments/my-credits/'),
  
  getCreditPacks: () =>
    api.get<any[]>('/payments/credit-packs/'),
  
  getPlans: () =>
    api.get<any[]>('/payments/plans/'),
  
  cancelSubscription: () =>
    api.post('/payments/cancel-subscription/'),
  
  getBillingPortal: () =>
    api.post<{ url: string }>('/payments/billing-portal/'),
};

// Analytics API
export const analyticsAPI = {
  getDashboard: (days?: number) => api.get('/analytics/dashboard/summary/', { params: { days: days || 30 } }),
  getTrends: (days?: number) => api.get('/analytics/dashboard/trends/', { params: { days: days || 30 } }),
  getListingStats: (id: string) => api.get(`/analytics/dashboard/listings/${id}/`),
  getPerformance: () => api.get('/analytics/dashboard/performance/'),
};

// Interface Notification
export interface Notification {
  id: string;
  type: 'message' | 'purchase' | 'sale' | 'favorite' | 'review' | 'subscription' | 'system';
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

// Notifications API
export const notificationsAPI = {
  getAll: (params?: { page?: number }) =>
    api.get<PaginatedResponse<Notification>>('/messages/notifications/', { params }),
  
  getOne: (id: string) =>
    api.get<Notification>(`/messages/notifications/${id}/`),
  
  markAsRead: (id: string) =>
    api.post(`/messages/notifications/${id}/mark_read/`),
  
  markAllAsRead: () =>
    api.post('/messages/notifications/mark_all_read/'),
  
  delete: (id: string) =>
    api.delete(`/messages/notifications/${id}/`),
  
  getUnreadCount: () =>
    api.get<{ unread_count: number }>('/messages/notifications/unread_count/'),
};

export default api;

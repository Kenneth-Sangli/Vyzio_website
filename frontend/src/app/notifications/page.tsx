'use client';

import { useState, useEffect } from 'react';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { useRouter } from 'next/navigation';
import { notificationsAPI, Notification } from '@/lib/api';
import {
  Bell,
  MessageSquare,
  ShoppingBag,
  Heart,
  Star,
  Check,
  Trash2,
  CheckCheck,
  DollarSign,
  CreditCard,
} from 'lucide-react';


export default function NotificationsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion');
      return;
    }
    fetchNotifications();
  }, [isAuthenticated]);

  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const response = await notificationsAPI.getAll();
      // L'API retourne directement un tableau, pas une structure paginée
      const data = response.data;
      setNotifications(Array.isArray(data) ? data : (data.results || []));
    } catch (error) {
      console.error('Error fetching notifications:', error);
      // Si l'API échoue, montrer un tableau vide
      setNotifications([]);
    } finally {
      setIsLoading(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await notificationsAPI.markAsRead(notificationId);
      setNotifications(prev =>
        prev.map(n => (n.id === notificationId ? { ...n, is_read: true } : n))
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationsAPI.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await notificationsAPI.delete(notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'message':
        return <MessageSquare className="h-5 w-5 text-blue-500" />;
      case 'purchase':
        return <ShoppingBag className="h-5 w-5 text-green-500" />;
      case 'sale':
        return <DollarSign className="h-5 w-5 text-emerald-500" />;
      case 'favorite':
        return <Heart className="h-5 w-5 text-red-500" />;
      case 'review':
        return <Star className="h-5 w-5 text-yellow-500" />;
      case 'subscription':
        return <CreditCard className="h-5 w-5 text-purple-500" />;
      default:
        return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const filteredNotifications = notifications.filter(n =>
    filter === 'all' ? true : !n.is_read
  );

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {/* En-tête */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
              <p className="text-gray-600">
                {unreadCount > 0
                  ? `${unreadCount} notification${unreadCount > 1 ? 's' : ''} non lue${unreadCount > 1 ? 's' : ''}`
                  : 'Toutes les notifications sont lues'}
              </p>
            </div>
            {unreadCount > 0 && (
              <Button variant="outline" onClick={markAllAsRead}>
                <CheckCheck className="h-4 w-4 mr-2" />
                Tout marquer comme lu
              </Button>
            )}
          </div>

          {/* Filtres */}
          <div className="flex gap-2 mb-6">
            <Button
              variant={filter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              Toutes ({notifications.length})
            </Button>
            <Button
              variant={filter === 'unread' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('unread')}
            >
              Non lues ({unreadCount})
            </Button>
          </div>

          {/* Liste des notifications */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Chargement...</p>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="bg-white rounded-xl p-12 text-center">
              <Bell className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Aucune notification
              </h3>
              <p className="text-gray-500">
                {filter === 'unread'
                  ? 'Vous avez lu toutes vos notifications'
                  : 'Vous n\'avez pas encore de notifications'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`bg-white rounded-xl p-4 shadow-sm border transition-all ${
                    notification.is_read
                      ? 'border-gray-100'
                      : 'border-indigo-200 bg-indigo-50/30'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      {getIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-gray-900">
                          {notification.title}
                        </h4>
                        <span className="text-xs text-gray-500">
                          {new Date(notification.created_at).toLocaleDateString('fr-FR')}
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm mt-1">
                        {notification.message}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {!notification.is_read && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => markAsRead(notification.id)}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteNotification(notification.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

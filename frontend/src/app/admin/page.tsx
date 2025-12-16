'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { api } from '@/lib/api';
import {
  Shield,
  Users,
  Package,
  MessageSquare,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Settings,
  LogOut,
  Home,
  BarChart3,
  FileText,
  Bell,
  Search,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AdminStats {
  total_users: number;
  total_listings: number;
  total_transactions: number;
  total_revenue: number;
  pending_listings: number;
  reported_items: number;
  new_users_today: number;
  active_users: number;
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/admin/login');
      return;
    }

    if (user && !user.is_superuser) {
      router.push('/');
      return;
    }

    fetchAdminStats();
  }, [isAuthenticated, user, router]);

  const fetchAdminStats = async () => {
    try {
      const response = await api.get('/admin/dashboard-stats/');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching admin stats:', error);
      // Utiliser des données par défaut si l'API n'existe pas encore
      setStats({
        total_users: 0,
        total_listings: 0,
        total_transactions: 0,
        total_revenue: 0,
        pending_listings: 0,
        reported_items: 0,
        new_users_today: 0,
        active_users: 0,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  const sidebarItems = [
    { name: 'Tableau de bord', icon: BarChart3, href: '/admin', active: true },
    { name: 'Utilisateurs', icon: Users, href: '/admin/users' },
    { name: 'Annonces', icon: Package, href: '/admin/listings' },
    { name: 'Transactions', icon: DollarSign, href: '/admin/transactions' },
    { name: 'Messages', icon: MessageSquare, href: '/admin/messages' },
    { name: 'Signalements', icon: AlertTriangle, href: '/admin/reports' },
    { name: 'Paramètres', icon: Settings, href: '/admin/settings' },
  ];

  const statCards = [
    {
      title: 'Utilisateurs totaux',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'bg-blue-500',
      change: `+${stats?.new_users_today || 0} aujourd'hui`,
    },
    {
      title: 'Annonces actives',
      value: stats?.total_listings || 0,
      icon: Package,
      color: 'bg-green-500',
      change: `${stats?.pending_listings || 0} en attente`,
    },
    {
      title: 'Transactions',
      value: stats?.total_transactions || 0,
      icon: TrendingUp,
      color: 'bg-purple-500',
      change: 'Ce mois',
    },
    {
      title: 'Revenus',
      value: `${(stats?.total_revenue || 0).toLocaleString()} €`,
      icon: DollarSign,
      color: 'bg-yellow-500',
      change: 'Ce mois',
    },
  ];

  if (!isAuthenticated || (user && !user.is_superuser)) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sidebar Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-gray-900 transform transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-600 rounded-lg">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">Admin</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-gray-400 hover:text-white"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <nav className="px-4 space-y-1">
          {sidebarItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                item.active
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
          <Link
            href="/"
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors mb-2"
          >
            <Home className="h-5 w-5" />
            <span>Retour au site</span>
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-red-400 hover:bg-red-900/30 hover:text-red-300 transition-colors w-full"
          >
            <LogOut className="h-5 w-5" />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Bar */}
        <header className="bg-white shadow-sm sticky top-0 z-30">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden text-gray-600 hover:text-gray-900"
              >
                <Menu className="h-6 w-6" />
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Tableau de bord</h1>
            </div>

            <div className="flex items-center gap-4">
              <button className="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-medium">
                  {user?.first_name?.[0] || 'A'}
                </div>
                <span className="text-sm font-medium text-gray-700 hidden sm:block">
                  {user?.first_name || 'Admin'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="p-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statCards.map((stat) => (
              <div
                key={stat.title}
                className="bg-white rounded-xl p-6 shadow-sm"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-lg ${stat.color}`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-gray-900">
                  {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                </h3>
                <p className="text-gray-500 text-sm">{stat.title}</p>
                <p className="text-xs text-gray-400 mt-2">{stat.change}</p>
              </div>
            ))}
          </div>

          {/* Quick Actions & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h2>
              <div className="space-y-3">
                <Link
                  href="/admin/listings?status=pending"
                  className="flex items-center justify-between p-3 rounded-lg bg-yellow-50 hover:bg-yellow-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-yellow-600" />
                    <span className="text-yellow-800">Annonces en attente</span>
                  </div>
                  <span className="bg-yellow-200 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium">
                    {stats?.pending_listings || 0}
                  </span>
                </Link>
                <Link
                  href="/admin/reports"
                  className="flex items-center justify-between p-3 rounded-lg bg-red-50 hover:bg-red-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                    <span className="text-red-800">Signalements</span>
                  </div>
                  <span className="bg-red-200 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                    {stats?.reported_items || 0}
                  </span>
                </Link>
                <Link
                  href="/admin/users"
                  className="flex items-center justify-between p-3 rounded-lg bg-green-50 hover:bg-green-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Users className="h-5 w-5 text-green-600" />
                    <span className="text-green-800">Nouveaux utilisateurs</span>
                  </div>
                  <span className="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                    {stats?.new_users_today || 0}
                  </span>
                </Link>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Activité récente</h2>
              <div className="space-y-4">
                {[
                  { icon: Users, text: 'Nouvel utilisateur inscrit', time: 'Il y a 5 min', color: 'text-blue-500' },
                  { icon: Package, text: 'Nouvelle annonce publiée', time: 'Il y a 12 min', color: 'text-green-500' },
                  { icon: DollarSign, text: 'Transaction effectuée', time: 'Il y a 25 min', color: 'text-purple-500' },
                  { icon: AlertTriangle, text: 'Signalement reçu', time: 'Il y a 1h', color: 'text-red-500' },
                  { icon: CheckCircle, text: 'Annonce approuvée', time: 'Il y a 2h', color: 'text-green-500' },
                ].map((activity, index) => (
                  <div key={index} className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50">
                    <div className={`p-2 rounded-lg bg-gray-100 ${activity.color}`}>
                      <activity.icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{activity.text}</p>
                      <p className="text-xs text-gray-500">{activity.time}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

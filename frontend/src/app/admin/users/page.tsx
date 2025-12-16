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
  AlertTriangle,
  Settings,
  LogOut,
  Home,
  BarChart3,
  Search,
  Menu,
  X,
  Ban,
  CheckCircle,
  MoreHorizontal,
  Eye,
  Mail,
  Calendar,
  UserCheck,
  UserX,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AdminUser {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  is_banned: boolean;
  is_verified: boolean;
  created_at: string;
}

export default function AdminUsersPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/admin/login');
      return;
    }

    if (user && !user.is_superuser) {
      router.push('/');
      return;
    }

    fetchUsers();
  }, [isAuthenticated, user, router]);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (roleFilter !== 'all') params.role = roleFilter;
      if (statusFilter === 'banned') params.is_banned = 'true';
      if (statusFilter === 'active') params.is_banned = 'false';
      
      const response = await api.get('/admin/users/', { params });
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user?.is_superuser) {
      fetchUsers();
    }
  }, [roleFilter, statusFilter]);

  const handleBanUser = async (userId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir bannir cet utilisateur ?')) return;
    
    try {
      await api.post('/admin/ban-user/', { user_id: userId, reason: 'Admin action' });
      fetchUsers();
    } catch (error) {
      console.error('Error banning user:', error);
    }
  };

  const handleUnbanUser = async (userId: string) => {
    try {
      await api.post('/admin/unban-user/', { user_id: userId });
      fetchUsers();
    } catch (error) {
      console.error('Error unbanning user:', error);
    }
  };

  const filteredUsers = users.filter(u => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      u.email?.toLowerCase().includes(query) ||
      u.username?.toLowerCase().includes(query) ||
      u.first_name?.toLowerCase().includes(query) ||
      u.last_name?.toLowerCase().includes(query)
    );
  });

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  const sidebarItems = [
    { name: 'Tableau de bord', icon: BarChart3, href: '/admin', active: false },
    { name: 'Utilisateurs', icon: Users, href: '/admin/users', active: true },
    { name: 'Annonces', icon: Package, href: '/admin/listings', active: false },
    { name: 'Transactions', icon: DollarSign, href: '/admin/transactions', active: false },
    { name: 'Signalements', icon: AlertTriangle, href: '/admin/reports', active: false },
    { name: 'Paramètres', icon: Settings, href: '/admin/settings', active: false },
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
            <Link href="/admin" className="flex items-center gap-3">
              <div className="p-2 bg-primary-600 rounded-lg">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">Admin</span>
            </Link>
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
              <h1 className="text-xl font-semibold text-gray-900">Gestion des utilisateurs</h1>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6">
          {/* Filters */}
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher par email, nom..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">Tous les rôles</option>
                <option value="buyer">Acheteurs</option>
                <option value="seller">Vendeurs</option>
                <option value="professional">Professionnels</option>
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">Tous les statuts</option>
                <option value="active">Actifs</option>
                <option value="banned">Bannis</option>
              </select>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Utilisateur</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Rôle</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Statut</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Inscription</th>
                    <th className="text-right py-4 px-6 font-medium text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-gray-500">
                        Chargement...
                      </td>
                    </tr>
                  ) : filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-gray-500">
                        Aucun utilisateur trouvé
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((u) => (
                      <tr key={u.id} className="hover:bg-gray-50">
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                              <span className="text-gray-600 font-medium">
                                {u.email?.[0]?.toUpperCase() || '?'}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{u.email}</p>
                              <p className="text-sm text-gray-500">
                                {u.first_name} {u.last_name}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            u.role === 'seller' ? 'bg-blue-100 text-blue-700' :
                            u.role === 'professional' ? 'bg-purple-100 text-purple-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {u.role === 'seller' ? 'Vendeur' :
                             u.role === 'professional' ? 'Pro' : 'Acheteur'}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          {u.is_banned ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                              <Ban className="h-3 w-3 mr-1" />
                              Banni
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Actif
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-500">
                          {new Date(u.created_at).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center justify-end gap-2">
                            <Link href={`/vendeur/${u.id}`}>
                              <Button variant="outline" size="sm">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </Link>
                            {u.is_banned ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleUnbanUser(u.id)}
                                className="text-green-600 hover:bg-green-50"
                              >
                                <UserCheck className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleBanUser(u.id)}
                                className="text-red-600 hover:bg-red-50"
                              >
                                <UserX className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

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
  DollarSign,
  AlertTriangle,
  Settings,
  LogOut,
  Home,
  BarChart3,
  Menu,
  X,
  Search,
  Clock,
  CheckCircle,
  XCircle,
  CreditCard,
} from 'lucide-react';

interface Transaction {
  id: string;
  amount: number;
  status: string;
  payment_intent_id: string;
  created_at: string;
  buyer: {
    id: string;
    email: string;
  };
  seller: {
    id: string;
    email: string;
  };
  listing: {
    id: string;
    title: string;
  };
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'bg-yellow-100 text-yellow-700' },
  completed: { label: 'Complété', color: 'bg-green-100 text-green-700' },
  failed: { label: 'Échoué', color: 'bg-red-100 text-red-700' },
  refunded: { label: 'Remboursé', color: 'bg-gray-100 text-gray-700' },
};

export default function AdminTransactionsPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/admin/login');
      return;
    }

    if (user && !user.is_superuser) {
      router.push('/');
      return;
    }

    fetchTransactions();
  }, [isAuthenticated, user, router]);

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/payments/transactions/');
      setTransactions(response.data.results || response.data || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setTransactions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  const sidebarItems = [
    { name: 'Tableau de bord', icon: BarChart3, href: '/admin', active: false },
    { name: 'Utilisateurs', icon: Users, href: '/admin/users', active: false },
    { name: 'Annonces', icon: Package, href: '/admin/listings', active: false },
    { name: 'Transactions', icon: DollarSign, href: '/admin/transactions', active: true },
    { name: 'Signalements', icon: AlertTriangle, href: '/admin/reports', active: false },
    { name: 'Paramètres', icon: Settings, href: '/admin/settings', active: false },
  ];

  const filteredTransactions = transactions.filter((t) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      t.buyer?.email?.toLowerCase().includes(query) ||
      t.seller?.email?.toLowerCase().includes(query) ||
      t.listing?.title?.toLowerCase().includes(query) ||
      t.payment_intent_id?.toLowerCase().includes(query)
    );
  });

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
              <h1 className="text-xl font-semibold text-gray-900">Transactions</h1>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6">
          {/* Search */}
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par email, annonce, ID paiement..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Transactions Table */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Transaction</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Acheteur</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Vendeur</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Montant</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Statut</th>
                    <th className="text-left py-4 px-6 font-medium text-gray-700">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-500">
                        Chargement...
                      </td>
                    </tr>
                  ) : filteredTransactions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-500">
                        <CreditCard className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                        Aucune transaction trouvée
                      </td>
                    </tr>
                  ) : (
                    filteredTransactions.map((t) => (
                      <tr key={t.id} className="hover:bg-gray-50">
                        <td className="py-4 px-6">
                          <div>
                            <p className="font-medium text-gray-900 truncate max-w-xs">
                              {t.listing?.title || 'N/A'}
                            </p>
                            <p className="text-xs text-gray-500 font-mono">
                              {t.payment_intent_id?.substring(0, 20)}...
                            </p>
                          </div>
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-600">
                          {t.buyer?.email || 'N/A'}
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-600">
                          {t.seller?.email || 'N/A'}
                        </td>
                        <td className="py-4 px-6">
                          <span className="font-semibold text-gray-900">
                            {t.amount?.toLocaleString('fr-FR')} €
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            STATUS_LABELS[t.status]?.color || 'bg-gray-100 text-gray-700'
                          }`}>
                            {t.status === 'completed' && <CheckCircle className="h-3 w-3 mr-1" />}
                            {t.status === 'failed' && <XCircle className="h-3 w-3 mr-1" />}
                            {t.status === 'pending' && <Clock className="h-3 w-3 mr-1" />}
                            {STATUS_LABELS[t.status]?.label || t.status}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-500">
                          {new Date(t.created_at).toLocaleDateString('fr-FR')}
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

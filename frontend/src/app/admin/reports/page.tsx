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
  Menu,
  X,
  CheckCircle,
  Eye,
  Clock,
  Flag,
  Ban,
  Trash2,
  AlertOctagon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Report {
  id: string;
  reason: string;
  description: string;
  status: string;
  created_at: string;
  reporter: {
    id: string;
    email: string;
    username: string;
  };
  reported_user: {
    id: string;
    email: string;
    username: string;
  };
  listing?: {
    id: string;
    title: string;
  };
  conversation?: {
    id: string;
  };
}

const REASON_LABELS: Record<string, string> = {
  spam: 'Spam',
  inappropriate: 'Contenu inapproprié',
  scam: 'Arnaque',
  offensive: 'Contenu offensant',
  other: 'Autre',
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'bg-yellow-100 text-yellow-700' },
  reviewed: { label: 'Examiné', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: 'Résolu', color: 'bg-green-100 text-green-700' },
  dismissed: { label: 'Rejeté', color: 'bg-gray-100 text-gray-700' },
};

export default function AdminReportsPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/admin/login');
      return;
    }

    if (user && !user.is_superuser) {
      router.push('/');
      return;
    }

    fetchReports();
  }, [isAuthenticated, user, router]);

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      
      const response = await api.get('/admin/reports/', { params });
      setReports(response.data.reports || []);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setReports([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user?.is_superuser) {
      fetchReports();
    }
  }, [statusFilter]);

  const handleResolveReport = async (reportId: string, action: string) => {
    try {
      await api.post('/admin/resolve-report/', { report_id: reportId, action });
      fetchReports();
      setSelectedReport(null);
    } catch (error) {
      console.error('Error resolving report:', error);
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
    { name: 'Transactions', icon: DollarSign, href: '/admin/transactions', active: false },
    { name: 'Signalements', icon: AlertTriangle, href: '/admin/reports', active: true },
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
              <h1 className="text-xl font-semibold text-gray-900">Signalements</h1>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6">
          {/* Filters */}
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
            <div className="flex flex-wrap gap-2">
              {['all', 'pending', 'reviewed', 'resolved', 'dismissed'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    statusFilter === status
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {status === 'all' ? 'Tous' : STATUS_LABELS[status]?.label || status}
                </button>
              ))}
            </div>
          </div>

          {/* Reports List */}
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Chargement...</div>
          ) : reports.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <Flag className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucun signalement trouvé</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reports.map((report) => (
                <div key={report.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <AlertOctagon className="h-5 w-5 text-red-500" />
                          <span className="font-semibold text-gray-900">
                            {REASON_LABELS[report.reason] || report.reason}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            STATUS_LABELS[report.status]?.color || 'bg-gray-100'
                          }`}>
                            {STATUS_LABELS[report.status]?.label || report.status}
                          </span>
                        </div>

                        <p className="text-gray-600 mb-4">{report.description}</p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Signalé par:</span>{' '}
                            <span className="font-medium">{report.reporter?.email}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Utilisateur signalé:</span>{' '}
                            <span className="font-medium">{report.reported_user?.email}</span>
                          </div>
                          {report.listing && (
                            <div>
                              <span className="text-gray-500">Annonce:</span>{' '}
                              <Link
                                href={`/annonces/${report.listing.id}`}
                                className="font-medium text-primary-600 hover:underline"
                              >
                                {report.listing.title}
                              </Link>
                            </div>
                          )}
                          <div>
                            <span className="text-gray-500">Date:</span>{' '}
                            <span className="font-medium">
                              {new Date(report.created_at).toLocaleDateString('fr-FR')}
                            </span>
                          </div>
                        </div>
                      </div>

                      {report.status === 'pending' && (
                        <div className="flex flex-col gap-2">
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                            onClick={() => handleResolveReport(report.id, 'resolved')}
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Résoudre
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => handleResolveReport(report.id, 'ban_user')}
                          >
                            <Ban className="h-4 w-4 mr-2" />
                            Bannir
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleResolveReport(report.id, 'dismissed')}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Rejeter
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

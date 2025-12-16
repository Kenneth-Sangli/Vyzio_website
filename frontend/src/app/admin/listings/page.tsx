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
  CheckCircle,
  XCircle,
  Eye,
  Clock,
  Tag,
  MapPin,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PendingListing {
  id: string;
  title: string;
  price: number;
  category: string;
  location: string;
  created_at: string;
  seller: {
    id: string;
    email: string;
    username: string;
  };
  images: { image: string }[];
}

export default function AdminListingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [listings, setListings] = useState<PendingListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/admin/login');
      return;
    }

    if (user && !user.is_superuser) {
      router.push('/');
      return;
    }

    fetchListings();
  }, [isAuthenticated, user, router]);

  const fetchListings = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/admin/pending-listings/');
      setListings(response.data.listings || []);
    } catch (error) {
      console.error('Error fetching listings:', error);
      setListings([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveListing = async (listingId: string) => {
    try {
      await api.post('/admin/approve-listing/', { listing_id: listingId });
      fetchListings();
    } catch (error) {
      console.error('Error approving listing:', error);
    }
  };

  const handleRejectListing = async (listingId: string) => {
    if (!rejectReason.trim()) {
      alert('Veuillez fournir une raison de rejet');
      return;
    }
    
    try {
      await api.post('/admin/reject-listing/', { listing_id: listingId, reason: rejectReason });
      setRejectingId(null);
      setRejectReason('');
      fetchListings();
    } catch (error) {
      console.error('Error rejecting listing:', error);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  const sidebarItems = [
    { name: 'Tableau de bord', icon: BarChart3, href: '/admin', active: false },
    { name: 'Utilisateurs', icon: Users, href: '/admin/users', active: false },
    { name: 'Annonces', icon: Package, href: '/admin/listings', active: true },
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
              <h1 className="text-xl font-semibold text-gray-900">Annonces en attente</h1>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Clock className="h-4 w-4" />
              <span>{listings.length} annonce(s) en attente</span>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6">
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Chargement...</div>
          ) : listings.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <Package className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Aucune annonce en attente de modération</p>
            </div>
          ) : (
            <div className="grid gap-6">
              {listings.map((listing) => (
                <div key={listing.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="flex flex-col md:flex-row">
                    {/* Image */}
                    <div className="w-full md:w-48 h-48 md:h-auto bg-gray-200 flex-shrink-0">
                      {listing.images?.[0] ? (
                        <img
                          src={listing.images[0].image}
                          alt={listing.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Package className="h-12 w-12 text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 p-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {listing.title}
                          </h3>
                          <p className="text-2xl font-bold text-primary-600 mb-4">
                            {listing.price?.toLocaleString('fr-FR')} €
                          </p>
                          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                            <span className="inline-flex items-center gap-1">
                              <Tag className="h-4 w-4" />
                              {listing.category}
                            </span>
                            <span className="inline-flex items-center gap-1">
                              <MapPin className="h-4 w-4" />
                              {listing.location}
                            </span>
                            <span className="inline-flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              {new Date(listing.created_at).toLocaleDateString('fr-FR')}
                            </span>
                          </div>
                          <div className="mt-4 text-sm">
                            <span className="text-gray-500">Vendeur:</span>{' '}
                            <span className="font-medium">{listing.seller?.email}</span>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col gap-2">
                          <Link href={`/annonces/${listing.id}`} target="_blank">
                            <Button variant="outline" size="sm" className="w-full">
                              <Eye className="h-4 w-4 mr-2" />
                              Voir
                            </Button>
                          </Link>
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                            onClick={() => handleApproveListing(listing.id)}
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approuver
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => setRejectingId(listing.id)}
                          >
                            <XCircle className="h-4 w-4 mr-2" />
                            Rejeter
                          </Button>
                        </div>
                      </div>

                      {/* Reject Modal */}
                      {rejectingId === listing.id && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Raison du rejet
                          </label>
                          <textarea
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder="Expliquez pourquoi cette annonce est rejetée..."
                            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            rows={3}
                          />
                          <div className="flex justify-end gap-2 mt-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setRejectingId(null);
                                setRejectReason('');
                              }}
                            >
                              Annuler
                            </Button>
                            <Button
                              size="sm"
                              className="bg-red-600 hover:bg-red-700"
                              onClick={() => handleRejectListing(listing.id)}
                            >
                              Confirmer le rejet
                            </Button>
                          </div>
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

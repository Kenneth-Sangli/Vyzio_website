'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { api } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import {
  Package,
  Truck,
  CheckCircle,
  Clock,
  AlertCircle,
  ChevronRight,
  MessageSquare,
  Search,
  Calendar,
  User,
  MapPin,
  Star,
  ExternalLink,
  ShoppingBag,
} from 'lucide-react';

interface Order {
  id: string;
  order_number: string;
  status: string;
  status_display: string;
  listing_title: string;
  listing_snapshot: {
    id: string;
    title: string;
    slug: string;
    price: string;
    condition: string;
    image: string | null;
  };
  item_price: string;
  seller_username: string;
  seller_email: string;
  delivery_type: string;
  tracking_number: string;
  carrier: string;
  tracking_url: string;
  created_at: string;
  shipped_at: string | null;
  delivered_at: string | null;
  completed_at: string | null;
  buyer_confirmed_receipt: boolean;
}

const statusConfig: Record<string, { color: string; icon: any; label: string; step: number }> = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'En attente', step: 1 },
  confirmed: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle, label: 'Confirmée', step: 1 },
  processing: { color: 'bg-blue-100 text-blue-800', icon: Package, label: 'En préparation', step: 2 },
  shipped: { color: 'bg-purple-100 text-purple-800', icon: Truck, label: 'Expédiée', step: 3 },
  delivered: { color: 'bg-green-100 text-green-800', icon: MapPin, label: 'Livrée', step: 4 },
  completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Terminée', step: 5 },
  cancelled: { color: 'bg-red-100 text-red-800', icon: AlertCircle, label: 'Annulée', step: 0 },
  refunded: { color: 'bg-orange-100 text-orange-800', icon: AlertCircle, label: 'Remboursée', step: 0 },
};

const deliverySteps = [
  { id: 1, label: 'Commande confirmée', icon: CheckCircle },
  { id: 2, label: 'En préparation', icon: Package },
  { id: 3, label: 'Expédiée', icon: Truck },
  { id: 4, label: 'Livrée', icon: MapPin },
  { id: 5, label: 'Terminée', icon: Star },
];

export default function MesAchatsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/mes-achats');
      return;
    }
    fetchOrders();
  }, [isAuthenticated]);

  const fetchOrders = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/orders/my-purchases/');
      setOrders(res.data.results || res.data || []);
    } catch (error) {
      console.error('Erreur chargement des achats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmReceipt = async (orderId: string) => {
    if (!confirm('Confirmez-vous avoir bien reçu votre commande ? Cette action libérera les fonds au vendeur.')) {
      return;
    }

    try {
      await api.post(`/orders/my-purchases/${orderId}/confirm-receipt/`);
      fetchOrders();
      alert('Réception confirmée ! Merci pour votre achat.');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la confirmation');
    }
  };

  const filteredOrders = orders.filter(order => {
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    const matchesSearch = order.listing_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.seller_username.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </span>
    );
  };

  const getStepProgress = (status: string) => {
    const config = statusConfig[status];
    return config?.step || 0;
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
              <Link href="/dashboard" className="hover:text-gray-700">Dashboard</Link>
              <ChevronRight className="h-4 w-4" />
              <span>Mes Achats</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Mes Achats</h1>
            <p className="text-gray-600 mt-1">
              Suivez vos commandes et confirmez vos réceptions
            </p>
          </div>
          <Link href="/recherche">
            <Button variant="gradient">
              <Search className="h-4 w-4 mr-2" />
              Continuer mes achats
            </Button>
          </Link>
        </div>

        {/* Filtres */}
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par titre, numéro ou vendeur..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tous les statuts</option>
              <option value="pending">En attente</option>
              <option value="confirmed">Confirmées</option>
              <option value="shipped">Expédiées</option>
              <option value="delivered">Livrées</option>
              <option value="completed">Terminées</option>
            </select>
          </div>
        </div>

        {/* Liste des commandes */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">Chargement...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
            <ShoppingBag className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun achat</h3>
            <p className="text-gray-500 mb-6">
              {orders.length === 0 
                ? "Vous n'avez pas encore effectué d'achat"
                : "Aucune commande ne correspond à vos filtres"
              }
            </p>
            <Link href="/recherche">
              <Button variant="gradient">
                Découvrir les annonces
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => (
              <div key={order.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="p-4 md:p-6">
                  <div className="flex flex-col md:flex-row md:items-start gap-4">
                    {/* Image */}
                    <div className="w-full md:w-24 h-24 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                      {order.listing_snapshot?.image ? (
                        <img
                          src={order.listing_snapshot.image}
                          alt={order.listing_title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-400">
                          <Package className="h-8 w-8" />
                        </div>
                      )}
                    </div>

                    {/* Infos principales */}
                    <div className="flex-1">
                      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs text-gray-500">#{order.order_number}</span>
                            {getStatusBadge(order.status)}
                          </div>
                          <h3 className="font-semibold text-gray-900">{order.listing_title}</h3>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-gray-900">
                            {formatPrice(parseFloat(order.item_price))}
                          </div>
                        </div>
                      </div>

                      {/* Détails */}
                      <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <User className="h-4 w-4" />
                          <span>Vendeur: {order.seller_username}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          <span>{new Date(order.created_at).toLocaleDateString('fr-FR')}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          {order.delivery_type === 'shipping' ? (
                            <><Truck className="h-4 w-4" /><span>Expédition</span></>
                          ) : (
                            <><MapPin className="h-4 w-4" /><span>Remise en main propre</span></>
                          )}
                        </div>
                      </div>

                      {/* Tracking */}
                      {order.tracking_number && (
                        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="text-sm text-blue-800">
                                <strong>Suivi:</strong> {order.tracking_number}
                                {order.carrier && ` (${order.carrier})`}
                              </span>
                            </div>
                            {order.tracking_url && (
                              <a
                                href={order.tracking_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                              >
                                Suivre <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Progress bar */}
                      {order.status !== 'cancelled' && order.status !== 'refunded' && (
                        <div className="mt-4">
                          <div className="flex justify-between mb-2">
                            {deliverySteps.slice(0, 4).map((step) => {
                              const isActive = getStepProgress(order.status) >= step.id;
                              const Icon = step.icon;
                              return (
                                <div key={step.id} className="flex flex-col items-center">
                                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                    isActive ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                                  }`}>
                                    <Icon className="h-4 w-4" />
                                  </div>
                                  <span className={`text-xs mt-1 hidden md:block ${
                                    isActive ? 'text-green-600 font-medium' : 'text-gray-400'
                                  }`}>
                                    {step.label}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500 transition-all duration-500"
                              style={{ width: `${Math.min((getStepProgress(order.status) / 4) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="mt-4 flex flex-wrap gap-2">
                        {(order.status === 'delivered' || order.status === 'shipped') && !order.buyer_confirmed_receipt && (
                          <Button
                            size="sm"
                            variant="gradient"
                            onClick={() => handleConfirmReceipt(order.id)}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Confirmer la réception
                          </Button>
                        )}
                        <Link href={`/messages?user=${order.seller_username}`}>
                          <Button size="sm" variant="outline">
                            <MessageSquare className="h-4 w-4 mr-1" />
                            Contacter le vendeur
                          </Button>
                        </Link>
                        {order.status === 'completed' && (
                          <Link href={`/vendeur/${order.seller_username}?review=true`}>
                            <Button size="sm" variant="outline">
                              <Star className="h-4 w-4 mr-1" />
                              Laisser un avis
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

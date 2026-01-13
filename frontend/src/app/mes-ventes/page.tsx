'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { api, formatPrice } from '@/lib/api';
import {
  Package,
  Truck,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowLeft,
  Eye,
  MessageSquare,
  Search,
  Filter,
  ChevronRight,
  MapPin,
  Calendar,
  User,
  Wallet,
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
  platform_fee: string;
  seller_amount: string;
  buyer_username: string;
  buyer_email: string;
  delivery_type: string;
  tracking_number: string;
  carrier: string;
  shipping_address: Record<string, string>;
  created_at: string;
  shipped_at: string | null;
  delivered_at: string | null;
  completed_at: string | null;
}

interface WalletData {
  balance: string;
  pending_balance: string;
  total_earned: string;
  total_withdrawn: string;
}

const statusConfig: Record<string, { color: string; icon: any; label: string }> = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'En attente' },
  confirmed: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle, label: 'Confirmée' },
  processing: { color: 'bg-blue-100 text-blue-800', icon: Package, label: 'En préparation' },
  shipped: { color: 'bg-purple-100 text-purple-800', icon: Truck, label: 'Expédiée' },
  delivered: { color: 'bg-green-100 text-green-800', icon: MapPin, label: 'Livrée' },
  completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Terminée' },
  cancelled: { color: 'bg-red-100 text-red-800', icon: AlertCircle, label: 'Annulée' },
  refunded: { color: 'bg-orange-100 text-orange-800', icon: AlertCircle, label: 'Remboursée' },
};

export default function MesVentesPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/mes-ventes');
      return;
    }
    fetchData();
  }, [isAuthenticated]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [ordersRes, walletRes] = await Promise.all([
        api.get('/orders/my-sales/'),
        api.get('/orders/wallet/me/').catch(() => ({ data: null })),
      ]);
      setOrders(ordersRes.data.results || ordersRes.data || []);
      setWallet(walletRes.data);
    } catch (error) {
      console.error('Erreur chargement des ventes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleShipOrder = async (orderId: string) => {
    const trackingNumber = prompt('Numéro de suivi (optionnel):');
    const carrier = prompt('Transporteur (ex: Colissimo, Mondial Relay):');
    
    try {
      await api.post(`/orders/my-sales/${orderId}/ship/`, {
        tracking_number: trackingNumber || '',
        carrier: carrier || '',
      });
      fetchData();
      alert('Commande marquée comme expédiée !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la mise à jour');
    }
  };

  const handleMarkDelivered = async (orderId: string) => {
    if (!confirm('Confirmer que la commande a été livrée ?')) return;
    
    try {
      await api.post(`/orders/my-sales/${orderId}/mark-delivered/`);
      fetchData();
      alert('Commande marquée comme livrée !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la mise à jour');
    }
  };

  const filteredOrders = orders.filter(order => {
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    const matchesSearch = order.listing_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.buyer_username.toLowerCase().includes(searchQuery.toLowerCase());
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
              <span>Mes Ventes</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Mes Ventes</h1>
            <p className="text-gray-600 mt-1">
              Gérez vos commandes et suivez vos revenus
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex gap-3">
            <Link href="/mes-ventes/wallet">
              <Button variant="outline">
                <Wallet className="h-4 w-4 mr-2" />
                Mon Portefeuille
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats rapides */}
        {wallet && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
              <div className="text-sm text-gray-500">Solde disponible</div>
              <div className="text-2xl font-bold text-green-600 mt-1">
                {formatPrice(parseFloat(wallet.balance))}
              </div>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
              <div className="text-sm text-gray-500">En attente</div>
              <div className="text-2xl font-bold text-yellow-600 mt-1">
                {formatPrice(parseFloat(wallet.pending_balance))}
              </div>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
              <div className="text-sm text-gray-500">Total gagné</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {formatPrice(parseFloat(wallet.total_earned))}
              </div>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
              <div className="text-sm text-gray-500">Total retiré</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {formatPrice(parseFloat(wallet.total_withdrawn))}
              </div>
            </div>
          </div>
        )}

        {/* Filtres */}
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par titre, numéro ou acheteur..."
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
              <option value="cancelled">Annulées</option>
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
            <Package className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune vente</h3>
            <p className="text-gray-500 mb-6">
              {orders.length === 0 
                ? "Vous n'avez pas encore réalisé de vente"
                : "Aucune commande ne correspond à vos filtres"
              }
            </p>
            <Link href="/mes-annonces/nouvelle">
              <Button variant="gradient">
                Créer une annonce
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
                          <div className="text-lg font-bold text-green-600">
                            +{formatPrice(parseFloat(order.seller_amount))}
                          </div>
                          <div className="text-xs text-gray-500">
                            (Prix: {formatPrice(parseFloat(order.item_price))})
                          </div>
                        </div>
                      </div>

                      {/* Détails */}
                      <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <User className="h-4 w-4" />
                          <span>{order.buyer_username}</span>
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
                        {order.tracking_number && (
                          <div className="flex items-center gap-1">
                            <Package className="h-4 w-4" />
                            <span>Suivi: {order.tracking_number}</span>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="mt-4 flex flex-wrap gap-2">
                        {(order.status === 'pending' || order.status === 'confirmed') && (
                          <Button
                            size="sm"
                            variant="gradient"
                            onClick={() => handleShipOrder(order.id)}
                          >
                            <Truck className="h-4 w-4 mr-1" />
                            Marquer comme expédiée
                          </Button>
                        )}
                        {order.status === 'shipped' && order.delivery_type === 'local' && (
                          <Button
                            size="sm"
                            variant="default"
                            onClick={() => handleMarkDelivered(order.id)}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Confirmer la livraison
                          </Button>
                        )}
                        <Link href={`/messages?user=${order.buyer_username}`}>
                          <Button size="sm" variant="outline">
                            <MessageSquare className="h-4 w-4 mr-1" />
                            Contacter l'acheteur
                          </Button>
                        </Link>
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

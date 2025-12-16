'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { analyticsAPI, listingsAPI, type Listing } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import {
  LayoutDashboard,
  PlusCircle,
  Eye,
  Heart,
  MessageSquare,
  TrendingUp,
  Package,
  DollarSign,
  Users,
  ArrowUpRight,
  ArrowDownRight,
  MoreHorizontal,
  Edit,
  Trash2,
  Zap,
  Settings,
  Search,
  ShoppingBag,
  Star,
  UserCircle,
} from 'lucide-react';

interface DashboardStats {
  total_views: number;
  total_favorites: number;
  total_messages: number;
  total_listings: number;
  active_listings: number;
  total_revenue: number;
  views_change: number;
  favorites_change: number;
}

// Dashboard pour les ACHETEURS
function BuyerDashboard({ user }: { user: any }) {
  const [favoriteListings, setFavoriteListings] = useState<Listing[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchBuyerData();
  }, []);

  const fetchBuyerData = async () => {
    try {
      const favRes = await listingsAPI.getFavorites();
      setFavoriteListings(favRes.data.results?.slice(0, 5) || []);
    } catch (error) {
      console.error('Error fetching buyer data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Bonjour, {user?.first_name || user?.username} 👋
          </h1>
          <p className="text-gray-600 mt-1">
            Découvrez les meilleures offres du moment
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex gap-3">
          <Link href="/recherche">
            <Button variant="gradient">
              <Search className="h-4 w-4 mr-2" />
              Rechercher
            </Button>
          </Link>
        </div>
      </div>

      {/* Buyer Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl bg-red-100 text-red-600">
              <Heart className="h-6 w-6" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">{favoriteListings.length}</h3>
          <p className="text-gray-500 text-sm">Articles en favoris</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl bg-green-100 text-green-600">
              <MessageSquare className="h-6 w-6" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">0</h3>
          <p className="text-gray-500 text-sm">Conversations actives</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-xl bg-blue-100 text-blue-600">
              <ShoppingBag className="h-6 w-6" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">0</h3>
          <p className="text-gray-500 text-sm">Achats effectués</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Favorite Listings */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Mes favoris</h2>
            <Link href="/favoris" className="text-primary-600 text-sm hover:underline">
              Voir tout
            </Link>
          </div>
          <div className="divide-y">
            {favoriteListings.length > 0 ? (
              favoriteListings.map((listing) => (
                <Link key={listing.id} href={`/annonces/${listing.id}`} className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                    {listing.images?.[0] ? (
                      <img
                        src={listing.images[0].image}
                        alt={listing.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <Package className="h-6 w-6" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">{listing.title}</h3>
                    <p className="text-sm text-primary-600 font-semibold">{formatPrice(listing.price)}</p>
                    <p className="text-xs text-gray-400">{listing.location}</p>
                  </div>
                  <Button variant="outline" size="sm">
                    Voir
                  </Button>
                </Link>
              ))
            ) : (
              <div className="p-8 text-center">
                <Heart className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Aucun favori pour le moment</p>
                <Link href="/recherche">
                  <Button variant="outline" className="mt-4">
                    Explorer les annonces
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions for Buyer */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h2>
            <div className="space-y-3">
              <Link href="/recherche" className="flex items-center p-3 rounded-xl bg-primary-50 hover:bg-primary-100 transition-colors">
                <Search className="h-5 w-5 text-primary-600 mr-3" />
                <span className="font-medium text-primary-700">Rechercher</span>
              </Link>
              <Link href="/favoris" className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors">
                <Heart className="h-5 w-5 text-gray-500 mr-3" />
                <span className="text-gray-700">Mes favoris</span>
              </Link>
              <Link href="/messages" className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors">
                <MessageSquare className="h-5 w-5 text-gray-500 mr-3" />
                <span className="text-gray-700">Mes messages</span>
              </Link>
              <Link href="/parametres" className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors">
                <Settings className="h-5 w-5 text-gray-500 mr-3" />
                <span className="text-gray-700">Paramètres</span>
              </Link>
            </div>
          </div>

          {/* Become Seller CTA */}
          <div className="bg-gradient-to-br from-primary-600 to-purple-600 rounded-2xl p-6 text-white">
            <h3 className="font-semibold mb-2">Devenez vendeur</h3>
            <p className="text-sm text-white/80 mb-4">
              Vous avez des articles à vendre ? Rejoignez notre communauté de vendeurs !
            </p>
            <ul className="text-sm space-y-2 mb-4">
              <li className="flex items-center">
                <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></span>
                Publiez vos annonces
              </li>
              <li className="flex items-center">
                <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></span>
                Touchez des milliers d'acheteurs
              </li>
              <li className="flex items-center">
                <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></span>
                Gérez vos ventes facilement
              </li>
            </ul>
            <Link href="/profil?upgrade=seller">
              <Button variant="secondary" className="w-full bg-white text-primary-600 hover:bg-gray-100">
                Devenir vendeur
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

// Dashboard pour les VENDEURS
function SellerDashboard({ user }: { user: any }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentListings, setRecentListings] = useState<Listing[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, listingsRes] = await Promise.all([
        analyticsAPI.getDashboard(),
        listingsAPI.getMyListings(),
      ]);
      setStats(statsRes.data);
      setRecentListings(listingsRes.data.results?.slice(0, 5) || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Vues totales',
      value: stats?.total_views || 0,
      change: stats?.views_change || 0,
      icon: Eye,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      title: 'Favoris',
      value: stats?.total_favorites || 0,
      change: stats?.favorites_change || 0,
      icon: Heart,
      color: 'bg-red-100 text-red-600',
    },
    {
      title: 'Messages',
      value: stats?.total_messages || 0,
      change: 0,
      icon: MessageSquare,
      color: 'bg-green-100 text-green-600',
    },
    {
      title: 'Annonces actives',
      value: stats?.active_listings || 0,
      change: 0,
      icon: Package,
      color: 'bg-purple-100 text-purple-600',
    },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Bonjour, {user?.first_name || user?.username} 👋
          </h1>
          <p className="text-gray-600 mt-1">
            Voici un aperçu de votre activité de vente
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex gap-3">
          <Link href="/annonces/nouvelle">
            <Button variant="gradient">
              <PlusCircle className="h-4 w-4 mr-2" />
              Nouvelle annonce
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => (
          <div key={stat.title} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
              {stat.change !== 0 && (
                <div className={`flex items-center text-sm ${stat.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.change > 0 ? (
                    <ArrowUpRight className="h-4 w-4" />
                  ) : (
                    <ArrowDownRight className="h-4 w-4" />
                  )}
                  <span>{Math.abs(stat.change)}%</span>
                </div>
              )}
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{stat.value.toLocaleString()}</h3>
            <p className="text-gray-500 text-sm">{stat.title}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Listings */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Mes annonces récentes</h2>
            <Link href="/mes-annonces" className="text-primary-600 text-sm hover:underline">
              Voir tout
            </Link>
          </div>
          <div className="divide-y">
            {recentListings.length > 0 ? (
              recentListings.map((listing) => (
                <div key={listing.id} className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                    {listing.images?.[0] ? (
                      <img
                        src={listing.images[0].image}
                        alt={listing.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <Package className="h-6 w-6" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">{listing.title}</h3>
                    <p className="text-sm text-gray-500">{formatPrice(listing.price)}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                      <span className="flex items-center">
                        <Eye className="h-3 w-3 mr-1" />
                        {listing.views_count}
                      </span>
                      <span className="flex items-center">
                        <Heart className="h-3 w-3 mr-1" />
                        {listing.favorites_count}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      listing.status === 'active' || listing.status === 'published' ? 'bg-green-100 text-green-700' :
                      listing.status === 'sold' ? 'bg-gray-100 text-gray-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {listing.status === 'active' || listing.status === 'published' ? 'Actif' :
                       listing.status === 'sold' ? 'Vendu' : 'Brouillon'}
                    </span>
                    <div className="relative group">
                      <button className="p-2 hover:bg-gray-100 rounded-lg">
                        <MoreHorizontal className="h-4 w-4 text-gray-400" />
                      </button>
                      <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                        <Link href={`/annonces/${listing.id}/modifier`} className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                          <Edit className="h-4 w-4 mr-2" />
                          Modifier
                        </Link>
                        <button className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 w-full">
                          <Zap className="h-4 w-4 mr-2" />
                          Booster
                        </button>
                        <button className="flex items-center px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Supprimer
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center">
                <Package className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Aucune annonce pour le moment</p>
                <Link href="/annonces/nouvelle">
                  <Button variant="outline" className="mt-4">
                    Créer ma première annonce
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions & Profile */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h2>
            <div className="space-y-3">
              <Link href="/annonces/nouvelle" className="flex items-center p-3 rounded-xl bg-primary-50 hover:bg-primary-100 transition-colors">
                <PlusCircle className="h-5 w-5 text-primary-600 mr-3" />
                <span className="font-medium text-primary-700">Créer une annonce</span>
              </Link>
              <Link href="/messages" className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors">
                <MessageSquare className="h-5 w-5 text-gray-500 mr-3" />
                <span className="text-gray-700">Voir mes messages</span>
              </Link>
              <Link href="/abonnements" className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors">
                <TrendingUp className="h-5 w-5 text-gray-500 mr-3" />
                <span className="text-gray-700">Gérer mon abonnement</span>
              </Link>
              <Link href="/parametres" className="flex items-center p-3 rounded-xl hover:bg-gray-50 transition-colors">
                <Settings className="h-5 w-5 text-gray-500 mr-3" />
                <span className="text-gray-700">Paramètres</span>
              </Link>
            </div>
          </div>

          {/* Subscription Card */}
          <div className="bg-gradient-to-br from-primary-600 to-purple-600 rounded-2xl p-6 text-white">
            <h3 className="font-semibold mb-2">Passez à Pro</h3>
            <p className="text-sm text-white/80 mb-4">
              Boostez votre visibilité avec un abonnement Pro
            </p>
            <ul className="text-sm space-y-2 mb-4">
              <li className="flex items-center">
                <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></span>
                Annonces illimitées
              </li>
              <li className="flex items-center">
                <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></span>
                Boost inclus
              </li>
              <li className="flex items-center">
                <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></span>
                Statistiques avancées
              </li>
            </ul>
            <Link href="/abonnements">
              <Button variant="secondary" className="w-full bg-white text-primary-600 hover:bg-gray-100">
                Découvrir
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  
  // Déterminer si l'utilisateur est un vendeur ou un acheteur
  const isSeller = user?.role === 'seller' || user?.role === 'professional' || user?.is_superuser;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1">
        {isSeller ? (
          <SellerDashboard user={user} />
        ) : (
          <BuyerDashboard user={user} />
        )}
      </main>

      <Footer />
    </div>
  );
}

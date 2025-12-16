'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { listingsAPI, type Listing } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import {
  PlusCircle,
  Eye,
  Heart,
  Package,
  MoreHorizontal,
  Edit,
  Trash2,
  Zap,
  Search,
  Filter,
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
} from 'lucide-react';

type StatusFilter = 'all' | 'active' | 'pending' | 'sold' | 'draft';

export default function MyListingsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [listings, setListings] = useState<Listing[]>([]);
  const [filteredListings, setFilteredListings] = useState<Listing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/mes-annonces');
      return;
    }
    
    if (user && user.role === 'buyer') {
      router.push('/dashboard');
      return;
    }
    
    fetchMyListings();
  }, [isAuthenticated, user, router]);

  useEffect(() => {
    filterListings();
  }, [listings, statusFilter, searchQuery]);

  const fetchMyListings = async () => {
    setIsLoading(true);
    try {
      const response = await listingsAPI.getMyListings();
      setListings(response.data.results || []);
    } catch (error) {
      console.error('Error fetching my listings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterListings = () => {
    let filtered = [...listings];

    // Filtre par statut
    if (statusFilter !== 'all') {
      filtered = filtered.filter(listing => {
        if (statusFilter === 'active') {
          return listing.status === 'active' || listing.status === 'published';
        }
        return listing.status === statusFilter;
      });
    }

    // Filtre par recherche
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(listing =>
        listing.title.toLowerCase().includes(query) ||
        listing.description?.toLowerCase().includes(query)
      );
    }

    setFilteredListings(filtered);
  };

  const handleDelete = async (listingId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette annonce ?')) {
      return;
    }
    
    try {
      await listingsAPI.delete(listingId);
      setListings(prev => prev.filter(l => l.id !== listingId));
    } catch (error) {
      console.error('Error deleting listing:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
      case 'published':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            Actif
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <Clock className="h-3 w-3 mr-1" />
            En attente
          </span>
        );
      case 'sold':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            Vendu
          </span>
        );
      case 'draft':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Edit className="h-3 w-3 mr-1" />
            Brouillon
          </span>
        );
      case 'archived':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <XCircle className="h-3 w-3 mr-1" />
            Archivé
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {status}
          </span>
        );
    }
  };

  const statusOptions: { value: StatusFilter; label: string; count: number }[] = [
    { value: 'all', label: 'Toutes', count: listings.length },
    { value: 'active', label: 'Actives', count: listings.filter(l => l.status === 'active' || l.status === 'published').length },
    { value: 'pending', label: 'En attente', count: listings.filter(l => l.status === 'pending').length },
    { value: 'sold', label: 'Vendues', count: listings.filter(l => l.status === 'sold').length },
    { value: 'draft', label: 'Brouillons', count: listings.filter(l => l.status === 'draft').length },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Mes annonces</h1>
            <p className="text-gray-600 mt-1">
              Gérez toutes vos annonces en un seul endroit
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <Link href="/annonces/nouvelle">
              <Button variant="gradient">
                <PlusCircle className="h-4 w-4 mr-2" />
                Nouvelle annonce
              </Button>
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher dans mes annonces..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Status Filter */}
            <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setStatusFilter(option.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    statusFilter === option.value
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {option.label} ({option.count})
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Listings */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
                <div className="flex gap-4">
                  <div className="w-24 h-24 bg-gray-200 rounded-lg" />
                  <div className="flex-1">
                    <div className="h-5 bg-gray-200 rounded w-1/3 mb-2" />
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-1/5" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredListings.length > 0 ? (
          <div className="space-y-4">
            {filteredListings.map((listing) => (
              <div
                key={listing.id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex gap-4">
                  {/* Image */}
                  <Link href={`/annonces/${listing.slug || listing.id}`} className="flex-shrink-0">
                    <div className="w-24 h-24 md:w-32 md:h-32 bg-gray-100 rounded-lg overflow-hidden">
                      {listing.images?.[0] ? (
                        <img
                          src={listing.images[0].image}
                          alt={listing.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-400">
                          <Package className="h-8 w-8" />
                        </div>
                      )}
                    </div>
                  </Link>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <Link href={`/annonces/${listing.slug || listing.id}`}>
                          <h3 className="font-semibold text-gray-900 hover:text-primary-600 transition-colors truncate">
                            {listing.title}
                          </h3>
                        </Link>
                        <p className="text-lg font-bold text-primary-600 mt-1">
                          {formatPrice(listing.price)}
                        </p>
                      </div>
                      {getStatusBadge(listing.status)}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                      <span className="flex items-center">
                        <Eye className="h-4 w-4 mr-1" />
                        {listing.views_count || 0} vues
                      </span>
                      <span className="flex items-center">
                        <Heart className="h-4 w-4 mr-1" />
                        {listing.favorites_count || 0} favoris
                      </span>
                      <span className="text-gray-400">
                        {listing.category?.name}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 mt-4">
                      <Link href={`/annonces/${listing.id}/modifier`}>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4 mr-1" />
                          Modifier
                        </Button>
                      </Link>
                      <Button variant="outline" size="sm">
                        <Zap className="h-4 w-4 mr-1" />
                        Booster
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => handleDelete(listing.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Supprimer
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
            <Package className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchQuery || statusFilter !== 'all'
                ? 'Aucune annonce trouvée'
                : 'Aucune annonce pour le moment'}
            </h3>
            <p className="text-gray-500 mb-6">
              {searchQuery || statusFilter !== 'all'
                ? 'Essayez de modifier vos filtres de recherche'
                : 'Créez votre première annonce et commencez à vendre !'}
            </p>
            {!searchQuery && statusFilter === 'all' && (
              <Link href="/annonces/nouvelle">
                <Button variant="gradient">
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Créer ma première annonce
                </Button>
              </Link>
            )}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

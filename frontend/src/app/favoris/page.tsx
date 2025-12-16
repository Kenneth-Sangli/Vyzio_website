'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { listingsAPI, type Listing } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from '@/hooks/use-toast';
import {
  Heart,
  Trash2,
  ExternalLink,
  Search,
  SlidersHorizontal,
} from 'lucide-react';

export default function FavoritesPage() {
  const { isAuthenticated } = useAuthStore();
  const [favorites, setFavorites] = useState<Listing[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      fetchFavorites();
    }
  }, [isAuthenticated]);

  const fetchFavorites = async () => {
    try {
      const response = await listingsAPI.getFavorites();
      setFavorites(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const removeFavorite = async (listingId: string) => {
    try {
      await listingsAPI.toggleFavorite(listingId);
      setFavorites((prev) => prev.filter((l) => l.id !== listingId));
      toast({
        title: 'Retiré des favoris',
        description: 'L\'annonce a été retirée de vos favoris',
      });
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de retirer des favoris',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Mes Favoris</h1>
              <p className="text-gray-600">
                {favorites.length} annonce{favorites.length > 1 ? 's' : ''} sauvegardée{favorites.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          ) : favorites.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Aucun favori pour le moment
              </h2>
              <p className="text-gray-500 mb-6">
                Parcourez les annonces et ajoutez vos préférées en favoris
              </p>
              <Link href="/annonces">
                <Button variant="gradient">
                  <Search className="w-4 h-4 mr-2" />
                  Parcourir les annonces
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {favorites.map((listing) => (
                <div
                  key={listing.id}
                  className="bg-white rounded-xl shadow-sm overflow-hidden group hover:shadow-md transition-shadow"
                >
                  <div className="relative aspect-[4/3]">
                    <img
                      src={listing.images[0]?.image || '/placeholder.jpg'}
                      alt={listing.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <button
                      onClick={() => removeFavorite(listing.id)}
                      className="absolute top-3 right-3 w-10 h-10 bg-white/90 backdrop-blur rounded-full flex items-center justify-center text-red-500 hover:bg-red-500 hover:text-white transition-colors"
                    >
                      <Heart className="w-5 h-5 fill-current" />
                    </button>
                    {listing.is_boosted && (
                      <span className="absolute top-3 left-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                        ⭐ Boost
                      </span>
                    )}
                  </div>
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 line-clamp-2 flex-1">
                        {listing.title}
                      </h3>
                    </div>
                    <p className="text-2xl font-bold text-primary-600 mb-2">
                      {listing.price.toLocaleString('fr-FR')} €
                    </p>
                    <p className="text-sm text-gray-500 mb-4">
                      📍 {listing.location}
                    </p>
                    <div className="flex gap-2">
                      <Link href={`/annonces/${listing.slug}`} className="flex-1">
                        <Button variant="outline" size="sm" className="w-full">
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Voir
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFavorite(listing.id)}
                        className="text-red-500 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
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

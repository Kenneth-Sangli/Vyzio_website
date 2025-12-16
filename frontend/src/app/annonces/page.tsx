'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { ListingCard, ListingCardSkeleton } from '@/components/listings';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { listingsAPI, categoriesAPI, type Listing, type Category } from '@/lib/api';
import {
  Search,
  SlidersHorizontal,
  Grid3X3,
  List,
  ChevronDown,
  X,
  MapPin,
} from 'lucide-react';

export default function ListingsPage() {
  const searchParams = useSearchParams();
  const [listings, setListings] = useState<Listing[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
    priceMin: '',
    priceMax: '',
    location: '',
    sort: 'recent',
  });

  // Mettre à jour les filtres quand les searchParams changent
  useEffect(() => {
    const q = searchParams.get('q') || '';
    const category = searchParams.get('category') || '';
    setFilters(prev => ({
      ...prev,
      q,
      category,
    }));
  }, [searchParams]);

  useEffect(() => {
    fetchCategories();
  }, []);

  // Refetch quand les filtres changent
  useEffect(() => {
    fetchListings();
  }, [filters.q, filters.category, filters.priceMin, filters.priceMax, filters.location, filters.sort]);

  const fetchListings = async () => {
    setIsLoading(true);
    try {
      const params: Record<string, any> = {};
      if (filters.q) params.search = filters.q;
      if (filters.category) params.category = filters.category;
      if (filters.priceMin) params.price_min = filters.priceMin;
      if (filters.priceMax) params.price_max = filters.priceMax;
      if (filters.location) params.location = filters.location;
      params.ordering = filters.sort === 'recent' ? '-created_at' : filters.sort === 'price_asc' ? 'price' : '-price';

      const response = await listingsAPI.getAll(params);
      setListings(response.data.results);
    } catch (error) {
      console.error('Error fetching listings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await categoriesAPI.getAll();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchListings();
  };

  const clearFilters = () => {
    setFilters({
      q: '',
      category: '',
      priceMin: '',
      priceMax: '',
      location: '',
      sort: 'recent',
    });
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1">
        {/* Search Header */}
        <div className="bg-white border-b sticky top-16 z-40">
          <div className="container mx-auto px-4 py-4">
            <form onSubmit={handleSearch} className="flex gap-4">
              <div className="flex-1 relative">
                <Input
                  type="search"
                  placeholder="Rechercher des annonces..."
                  value={filters.q}
                  onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                  icon={<Search className="h-5 w-5" />}
                />
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2"
              >
                <SlidersHorizontal className="h-4 w-4" />
                Filtres
                {Object.values(filters).filter(Boolean).length > 1 && (
                  <span className="bg-primary-500 text-white text-xs rounded-full px-2 py-0.5">
                    {Object.values(filters).filter(Boolean).length - 1}
                  </span>
                )}
              </Button>
              <Button type="submit" variant="gradient">
                Rechercher
              </Button>
            </form>

            {/* Filters Panel */}
            {showFilters && (
              <div className="mt-4 p-4 bg-gray-50 rounded-xl animate-in slide-in-from-top">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Catégorie
                    </label>
                    <select
                      value={filters.category}
                      onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                      className="w-full rounded-lg border-gray-300 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Toutes les catégories</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.slug}>{cat.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prix min
                    </label>
                    <Input
                      type="number"
                      placeholder="0 €"
                      value={filters.priceMin}
                      onChange={(e) => setFilters({ ...filters, priceMin: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prix max
                    </label>
                    <Input
                      type="number"
                      placeholder="10000 €"
                      value={filters.priceMax}
                      onChange={(e) => setFilters({ ...filters, priceMax: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Localisation
                    </label>
                    <Input
                      type="text"
                      placeholder="Ville ou code postal"
                      value={filters.location}
                      onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                      icon={<MapPin className="h-4 w-4" />}
                    />
                  </div>
                </div>
                <div className="flex justify-between items-center mt-4 pt-4 border-t">
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Réinitialiser les filtres
                  </button>
                  <Button onClick={fetchListings} size="sm">
                    Appliquer
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Results */}
        <div className="container mx-auto px-4 py-8">
          {/* Results Header */}
          <div className="flex items-center justify-between mb-6">
            <p className="text-gray-600">
              <span className="font-semibold text-gray-900">{listings.length}</span> annonces trouvées
            </p>
            <div className="flex items-center gap-4">
              {/* Sort */}
              <select
                value={filters.sort}
                onChange={(e) => {
                  setFilters({ ...filters, sort: e.target.value });
                  fetchListings();
                }}
                className="rounded-lg border-gray-300 text-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="recent">Plus récentes</option>
                <option value="price_asc">Prix croissant</option>
                <option value="price_desc">Prix décroissant</option>
              </select>

              {/* View Mode */}
              <div className="flex border rounded-lg overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-400'}`}
                >
                  <Grid3X3 className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-400'}`}
                >
                  <List className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Listings Grid */}
          {isLoading ? (
            <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' : 'grid-cols-1'}`}>
              {[...Array(8)].map((_, i) => (
                <ListingCardSkeleton key={i} />
              ))}
            </div>
          ) : listings.length > 0 ? (
            <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' : 'grid-cols-1'}`}>
              {listings.map((listing) => (
                <ListingCard
                  key={listing.id}
                  listing={listing}
                  variant={viewMode === 'list' ? 'horizontal' : 'default'}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="h-10 w-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Aucune annonce trouvée
              </h3>
              <p className="text-gray-600 mb-6">
                Essayez de modifier vos critères de recherche
              </p>
              <Button onClick={clearFilters} variant="outline">
                Réinitialiser les filtres
              </Button>
            </div>
          )}

          {/* Load More */}
          {listings.length > 0 && (
            <div className="text-center mt-12">
              <Button variant="outline" size="lg">
                Charger plus d'annonces
              </Button>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

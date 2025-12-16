'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { listingsAPI, categoriesAPI, type Listing, type Category } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import Image from 'next/image';
import {
  Search,
  Filter,
  MapPin,
  Grid,
  List,
  ChevronDown,
  X,
  SlidersHorizontal,
} from 'lucide-react';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [listings, setListings] = useState<Listing[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  
  // Filtres
  const [filters, setFilters] = useState({
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
    location: searchParams.get('location') || '',
    price_min: searchParams.get('price_min') || '',
    price_max: searchParams.get('price_max') || '',
    condition: searchParams.get('condition') || '',
    listing_type: searchParams.get('listing_type') || '',
    ordering: searchParams.get('ordering') || '-created_at',
  });

  const fetchCategories = useCallback(async () => {
    try {
      const response = await categoriesAPI.getAll();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  }, []);

  const fetchListings = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params[key] = value;
      });
      
      const response = await listingsAPI.getAll(params);
      setListings(response.data.results);
      setTotalCount(response.data.count);
    } catch (error) {
      console.error('Error fetching listings:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    fetchListings();
  }, [fetchListings]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    router.push(`/recherche?${params.toString()}`);
    fetchListings();
  };

  const clearFilters = () => {
    setFilters({
      q: '',
      category: '',
      location: '',
      price_min: '',
      price_max: '',
      condition: '',
      listing_type: '',
      ordering: '-created_at',
    });
  };

  const conditions = [
    { value: '', label: 'Tous' },
    { value: 'new', label: 'Neuf' },
    { value: 'like_new', label: 'Comme neuf' },
    { value: 'good', label: 'Bon état' },
    { value: 'fair', label: 'État correct' },
    { value: 'poor', label: 'Usé' },
  ];

  const listingTypes = [
    { value: '', label: 'Tous' },
    { value: 'product', label: 'Produit' },
    { value: 'service', label: 'Service' },
    { value: 'rental', label: 'Location' },
  ];

  const sortOptions = [
    { value: '-created_at', label: 'Plus récent' },
    { value: 'created_at', label: 'Plus ancien' },
    { value: 'price', label: 'Prix croissant' },
    { value: '-price', label: 'Prix décroissant' },
    { value: '-views_count', label: 'Popularité' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4">
          {/* Barre de recherche */}
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Rechercher..."
                  value={filters.q}
                  onChange={(e) => handleFilterChange('q', e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex-1 relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Localisation"
                  value={filters.location}
                  onChange={(e) => handleFilterChange('location', e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button onClick={applyFilters} className="bg-primary-600 hover:bg-primary-700">
                <Search className="h-4 w-4 mr-2" />
                Rechercher
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setShowFilters(!showFilters)}
                className="md:hidden"
              >
                <SlidersHorizontal className="h-4 w-4 mr-2" />
                Filtres
              </Button>
            </div>
          </div>

          <div className="flex gap-6">
            {/* Filtres latéraux */}
            <aside className={`w-64 shrink-0 ${showFilters ? 'block' : 'hidden'} md:block`}>
              <div className="bg-white rounded-lg shadow-sm p-4 sticky top-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg">Filtres</h3>
                  <button onClick={clearFilters} className="text-sm text-primary-600 hover:underline">
                    Effacer
                  </button>
                </div>

                {/* Catégorie */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Catégorie</label>
                  <select
                    value={filters.category}
                    onChange={(e) => handleFilterChange('category', e.target.value)}
                    className="w-full border rounded-md p-2"
                  >
                    <option value="">Toutes les catégories</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>

                {/* Type d'annonce */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Type</label>
                  <select
                    value={filters.listing_type}
                    onChange={(e) => handleFilterChange('listing_type', e.target.value)}
                    className="w-full border rounded-md p-2"
                  >
                    {listingTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>

                {/* État */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">État</label>
                  <select
                    value={filters.condition}
                    onChange={(e) => handleFilterChange('condition', e.target.value)}
                    className="w-full border rounded-md p-2"
                  >
                    {conditions.map(cond => (
                      <option key={cond.value} value={cond.value}>{cond.label}</option>
                    ))}
                  </select>
                </div>

                {/* Prix */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Prix</label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      placeholder="Min"
                      value={filters.price_min}
                      onChange={(e) => handleFilterChange('price_min', e.target.value)}
                    />
                    <Input
                      type="number"
                      placeholder="Max"
                      value={filters.price_max}
                      onChange={(e) => handleFilterChange('price_max', e.target.value)}
                    />
                  </div>
                </div>

                <Button onClick={applyFilters} className="w-full bg-primary-600 hover:bg-primary-700">
                  Appliquer les filtres
                </Button>
              </div>
            </aside>

            {/* Résultats */}
            <div className="flex-1">
              {/* En-tête résultats */}
              <div className="bg-white rounded-lg shadow-sm p-4 mb-4 flex items-center justify-between">
                <p className="text-gray-600">
                  <span className="font-semibold">{totalCount}</span> résultat{totalCount > 1 ? 's' : ''}
                </p>
                <div className="flex items-center gap-4">
                  <select
                    value={filters.ordering}
                    onChange={(e) => {
                      handleFilterChange('ordering', e.target.value);
                      setTimeout(fetchListings, 0);
                    }}
                    className="border rounded-md p-2 text-sm"
                  >
                    {sortOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                  <div className="flex border rounded-md">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`p-2 ${viewMode === 'grid' ? 'bg-gray-100' : ''}`}
                    >
                      <Grid className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      className={`p-2 ${viewMode === 'list' ? 'bg-gray-100' : ''}`}
                    >
                      <List className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Grille de résultats */}
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
              ) : listings.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                  <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Aucun résultat</h3>
                  <p className="text-gray-600">Essayez de modifier vos critères de recherche</p>
                </div>
              ) : (
                <div className={viewMode === 'grid' 
                  ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'
                  : 'space-y-4'
                }>
                  {listings.map((listing) => (
                    <Link
                      key={listing.id}
                      href={`/annonces/${listing.slug || listing.id}`}
                      className={`bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow ${
                        viewMode === 'list' ? 'flex' : ''
                      }`}
                    >
                      <div className={viewMode === 'list' ? 'w-48 h-36' : 'aspect-[4/3]'}>
                        {listing.images?.[0] ? (
                          <img
                            src={listing.images[0].image}
                            alt={listing.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                            <span className="text-gray-400">Pas d'image</span>
                          </div>
                        )}
                      </div>
                      <div className="p-4 flex-1">
                        <h3 className="font-semibold text-gray-900 line-clamp-1">{listing.title}</h3>
                        <p className="text-primary-600 font-bold text-lg mt-1">{listing.price} €</p>
                        <div className="flex items-center text-gray-500 text-sm mt-2">
                          <MapPin className="h-4 w-4 mr-1" />
                          {listing.location}
                        </div>
                        {viewMode === 'list' && (
                          <p className="text-gray-600 text-sm mt-2 line-clamp-2">
                            {listing.description}
                          </p>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

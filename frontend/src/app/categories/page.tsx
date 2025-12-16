'use client';

import { useState, useEffect, useCallback } from 'react';
import { Header, Footer } from '@/components/layout';
import { listingsAPI, categoriesAPI, type Listing, type Category } from '@/lib/api';
import Link from 'next/link';
import { MapPin, Grid, ChevronRight } from 'lucide-react';

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await categoriesAPI.getAll();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const categoryIcons: Record<string, string> = {
    'electronique': '📱',
    'vehicules': '🚗',
    'immobilier': '🏠',
    'mode': '👕',
    'maison': '🏡',
    'loisirs': '🎮',
    'services': '🛠️',
    'emploi': '💼',
    'autres': '📦',
  };

  const getCategoryIcon = (slug: string) => {
    return categoryIcons[slug] || '📦';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold mb-8">Toutes les catégories</h1>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {categories.map((category) => (
              <Link
                key={category.id}
                href={`/recherche?category=${category.id}`}
                className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow group"
              >
                <div className="flex items-center gap-4">
                  <div className="text-4xl">
                    {getCategoryIcon(category.slug)}
                  </div>
                  <div className="flex-1">
                    <h2 className="font-semibold text-lg group-hover:text-primary-600 transition-colors">
                      {category.name}
                    </h2>
                    {category.children && category.children.length > 0 && (
                      <p className="text-sm text-gray-500">
                        {category.children.length} sous-catégories
                      </p>
                    )}
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
                </div>

                {/* Sous-catégories */}
                {category.children && category.children.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="flex flex-wrap gap-2">
                      {category.children.slice(0, 4).map((child) => (
                        <span
                          key={child.id}
                          className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                        >
                          {child.name}
                        </span>
                      ))}
                      {category.children.length > 4 && (
                        <span className="text-xs text-gray-500">
                          +{category.children.length - 4} autres
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </Link>
            ))}
          </div>

          {categories.length === 0 && (
            <div className="text-center py-12">
              <Grid className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Aucune catégorie</h2>
              <p className="text-gray-600">Les catégories seront bientôt disponibles</p>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

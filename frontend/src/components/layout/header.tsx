'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  Menu,
  X,
  User,
  Heart,
  MessageSquare,
  PlusCircle,
  ChevronDown,
  LogOut,
  Settings,
  LayoutDashboard,
  Bell,
} from 'lucide-react';

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/annonces?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">V</span>
            </div>
            <span className="font-bold text-xl bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
              Vyzio
            </span>
          </Link>

          {/* Search Bar - Desktop */}
          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-xl mx-8">
            <div className="relative w-full">
              <Input
                type="search"
                placeholder="Rechercher des annonces..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                icon={<Search className="h-5 w-5" />}
                className="pr-4"
              />
            </div>
          </form>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-4">
            <Link href="/annonces" className="text-gray-600 hover:text-gray-900 transition-colors">
              Parcourir
            </Link>
            
            {isAuthenticated ? (
              <>
                <Link href="/messages" className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors">
                  <MessageSquare className="h-5 w-5" />
                  <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
                </Link>
                
                <Link href="/favoris" className="p-2 text-gray-600 hover:text-gray-900 transition-colors">
                  <Heart className="h-5 w-5" />
                </Link>
                
                <Link href="/notifications" className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors">
                  <Bell className="h-5 w-5" />
                </Link>

                {/* Bouton visible seulement pour les vendeurs */}
                {(user?.role === 'seller' || user?.role === 'professional' || user?.is_superuser) && (
                  <Link href="/annonces/nouvelle">
                    <Button variant="gradient" size="sm">
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Déposer une annonce
                    </Button>
                  </Link>
                )}

                {/* User Menu */}
                <div className="relative">
                  <button
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      {user?.avatar ? (
                        <img src={user.avatar} alt="" className="w-8 h-8 rounded-full object-cover" />
                      ) : (
                        <User className="h-4 w-4 text-primary-600" />
                      )}
                    </div>
                    <ChevronDown className="h-4 w-4 text-gray-500" />
                  </button>

                  {isUserMenuOpen && (
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border py-2 animate-in fade-in slide-in-from-top-2">
                      <div className="px-4 py-2 border-b">
                        <p className="font-medium">{user?.first_name || user?.username}</p>
                        <p className="text-sm text-gray-500">{user?.email}</p>
                      </div>
                      <Link href="/dashboard" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors">
                        <LayoutDashboard className="h-4 w-4 mr-3" />
                        Tableau de bord
                      </Link>
                      {/* Mes annonces - visible seulement pour les vendeurs */}
                      {(user?.role === 'seller' || user?.role === 'professional' || user?.is_superuser) && (
                        <Link href="/mes-annonces" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors">
                          <PlusCircle className="h-4 w-4 mr-3" />
                          Mes annonces
                        </Link>
                      )}
                      <Link href="/profil" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors">
                        <User className="h-4 w-4 mr-3" />
                        Mon profil
                      </Link>
                      <Link href="/parametres" className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors">
                        <Settings className="h-4 w-4 mr-3" />
                        Paramètres
                      </Link>
                      <hr className="my-2" />
                      <button
                        onClick={logout}
                        className="flex items-center w-full px-4 py-2 text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <LogOut className="h-4 w-4 mr-3" />
                        Déconnexion
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <Link href="/connexion">
                  <Button variant="ghost">Connexion</Button>
                </Link>
                <Link href="/inscription">
                  <Button variant="gradient">S'inscrire</Button>
                </Link>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2"
          >
            {isMobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>

        {/* Mobile Search */}
        <div className="md:hidden pb-4">
          <form onSubmit={handleSearch}>
            <Input
              type="search"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search className="h-5 w-5" />}
            />
          </form>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t bg-white animate-in slide-in-from-top">
          <nav className="container mx-auto px-4 py-4 space-y-2">
            <Link href="/annonces" className="block px-4 py-2 rounded-lg hover:bg-gray-50">
              Parcourir les annonces
            </Link>
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="block px-4 py-2 rounded-lg hover:bg-gray-50">
                  Tableau de bord
                </Link>
                {/* Mes annonces - visible seulement pour les vendeurs */}
                {(user?.role === 'seller' || user?.role === 'professional' || user?.is_superuser) && (
                  <Link href="/mes-annonces" className="block px-4 py-2 rounded-lg hover:bg-gray-50">
                    Mes annonces
                  </Link>
                )}
                <Link href="/messages" className="block px-4 py-2 rounded-lg hover:bg-gray-50">
                  Messages
                </Link>
                <Link href="/favoris" className="block px-4 py-2 rounded-lg hover:bg-gray-50">
                  Favoris
                </Link>
                <Link href="/profil" className="block px-4 py-2 rounded-lg hover:bg-gray-50">
                  Mon profil
                </Link>
                <hr className="my-2" />
                {/* Déposer une annonce - visible seulement pour les vendeurs */}
                {(user?.role === 'seller' || user?.role === 'professional' || user?.is_superuser) && (
                  <Link href="/annonces/nouvelle" className="block">
                    <Button variant="gradient" className="w-full">
                      <PlusCircle className="h-4 w-4 mr-2" />
                      Déposer une annonce
                    </Button>
                  </Link>
                )}
                <button
                  onClick={logout}
                  className="w-full text-left px-4 py-2 text-red-600 rounded-lg hover:bg-red-50"
                >
                  Déconnexion
                </button>
              </>
            ) : (
              <>
                <Link href="/connexion" className="block">
                  <Button variant="outline" className="w-full">Connexion</Button>
                </Link>
                <Link href="/inscription" className="block">
                  <Button variant="gradient" className="w-full">S'inscrire</Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

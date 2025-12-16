'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useAuthStore } from '@/stores/auth-store';
import { authAPI } from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Camera,
  Save,
  Shield,
  Bell,
  CreditCard,
  LogOut,
} from 'lucide-react';

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, updateUser } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    bio: '',
    location: '',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/profil');
      return;
    }
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        bio: user.bio || '',
        location: user.location || '',
      });
    }
  }, [isAuthenticated, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await authAPI.updateProfile(formData);
      updateUser(response.data);
      toast({
        title: 'Profil mis à jour',
        description: 'Vos informations ont été enregistrées',
        variant: 'success',
      });
    } catch (error: any) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.message || 'Une erreur est survenue',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const tabs = [
    { id: 'profile', label: 'Profil', icon: User },
    { id: 'security', label: 'Sécurité', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'payment', label: 'Paiement', icon: CreditCard },
  ];

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="flex items-center gap-6">
              <div className="relative">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center text-white text-3xl font-bold">
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt={user.username}
                      className="w-full h-full rounded-full object-cover"
                    />
                  ) : (
                    user.first_name?.charAt(0) || user.email.charAt(0).toUpperCase()
                  )}
                </div>
                <button className="absolute bottom-0 right-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white hover:bg-primary-700 transition-colors">
                  <Camera className="w-4 h-4" />
                </button>
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900">
                  {user.first_name} {user.last_name}
                </h1>
                <p className="text-gray-500">@{user.username}</p>
                <div className="flex items-center gap-4 mt-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    user.subscription_type === 'pro'
                      ? 'bg-purple-100 text-purple-700'
                      : user.subscription_type === 'basic'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {user.subscription_type === 'pro' ? 'Pro' : user.subscription_type === 'basic' ? 'Basic' : 'Gratuit'}
                  </span>
                  {user.is_verified && (
                    <span className="flex items-center gap-1 text-green-600 text-sm">
                      <Shield className="w-4 h-4" />
                      Vérifié
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-6">
            {/* Sidebar */}
            <div className="w-64 shrink-0">
              <div className="bg-white rounded-xl shadow-sm p-4">
                <nav className="space-y-1">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                        activeTab === tab.id
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <tab.icon className="w-5 h-5" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  ))}
                  <hr className="my-4" />
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="w-5 h-5" />
                    <span className="font-medium">Déconnexion</span>
                  </button>
                </nav>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1">
              {activeTab === 'profile' && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-6">Informations personnelles</h2>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                          Prénom
                        </label>
                        <Input
                          value={formData.first_name}
                          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                          placeholder="Votre prénom"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                          Nom
                        </label>
                        <Input
                          value={formData.last_name}
                          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                          placeholder="Votre nom"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Email
                      </label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        icon={<Mail className="w-5 h-5" />}
                        disabled
                      />
                      <p className="text-sm text-gray-500 mt-1">
                        L'email ne peut pas être modifié
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Téléphone
                      </label>
                      <Input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        icon={<Phone className="w-5 h-5" />}
                        placeholder="+33 6 12 34 56 78"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Localisation
                      </label>
                      <Input
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        icon={<MapPin className="w-5 h-5" />}
                        placeholder="Paris, France"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        Bio
                      </label>
                      <Textarea
                        value={formData.bio}
                        onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                        placeholder="Parlez-nous de vous..."
                        rows={4}
                      />
                    </div>

                    <div className="flex justify-end">
                      <Button type="submit" variant="gradient" loading={isLoading}>
                        <Save className="w-4 h-4 mr-2" />
                        Enregistrer
                      </Button>
                    </div>
                  </form>
                </div>
              )}

              {activeTab === 'security' && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-6">Sécurité</h2>
                  <div className="space-y-6">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h3 className="font-medium mb-2">Changer le mot de passe</h3>
                      <p className="text-sm text-gray-500 mb-4">
                        Nous vous recommandons d'utiliser un mot de passe fort et unique
                      </p>
                      <Button variant="outline">Modifier le mot de passe</Button>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h3 className="font-medium mb-2">Authentification à deux facteurs</h3>
                      <p className="text-sm text-gray-500 mb-4">
                        Ajoutez une couche de sécurité supplémentaire à votre compte
                      </p>
                      <Button variant="outline">Activer 2FA</Button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-6">Notifications</h2>
                  <div className="space-y-4">
                    {[
                      { label: 'Nouveaux messages', description: 'Recevez un email pour chaque nouveau message' },
                      { label: 'Nouvelles offres', description: 'Soyez notifié des offres sur vos annonces' },
                      { label: 'Newsletter', description: 'Recevez nos dernières actualités' },
                      { label: 'Alertes de prix', description: 'Soyez averti des baisses de prix sur vos favoris' },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <h3 className="font-medium">{item.label}</h3>
                          <p className="text-sm text-gray-500">{item.description}</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input type="checkbox" className="sr-only peer" defaultChecked />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'payment' && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-6">Moyens de paiement</h2>
                  <div className="text-center py-12">
                    <CreditCard className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="font-medium text-gray-900 mb-2">
                      Aucun moyen de paiement enregistré
                    </h3>
                    <p className="text-gray-500 mb-6">
                      Ajoutez une carte pour effectuer des achats plus rapidement
                    </p>
                    <Button variant="gradient">Ajouter une carte</Button>
                  </div>
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

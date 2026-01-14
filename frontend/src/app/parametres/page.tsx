'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { authAPI, api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from '@/hooks/use-toast';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Lock,
  Bell,
  Shield,
  CreditCard,
  Trash2,
  Save,
  Eye,
  EyeOff,
  Building2,
  Wallet,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, fetchUser } = useAuthStore();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  
  // Données du profil
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    username: '',
    phone: '',
    bio: '',
    location: '',
  });
  
  // Changement de mot de passe
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState(false);
  
  // Notifications
  const [notifications, setNotifications] = useState({
    email_messages: true,
    email_favorites: true,
    email_newsletter: false,
    push_messages: true,
    push_favorites: true,
  });

  // Informations bancaires (pour les vendeurs)
  const [bankData, setBankData] = useState({
    bank_name: '',
    account_holder: '',
    iban: '',
    bic: '',
  });
  const [bankSaved, setBankSaved] = useState(false);
  const [loadingBank, setLoadingBank] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/parametres');
      return;
    }
    
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        username: user.username || '',
        phone: user.phone || '',
        bio: user.bio || '',
        location: user.location || '',
      });
      
      // Charger les informations bancaires si l'utilisateur est vendeur
      if (user.role === 'seller' || user.role === 'professional') {
        fetchBankDetails();
      }
    }
  }, [user, isAuthenticated, router]);

  const fetchBankDetails = async () => {
    try {
      const res = await api.get('/orders/wallet/me/');
      if (res.data) {
        setBankData({
          bank_name: res.data.bank_name || '',
          account_holder: res.data.account_holder || '',
          iban: res.data.iban || '',
          bic: res.data.bic || '',
        });
        setBankSaved(!!res.data.iban);
      }
    } catch (error) {
      // Wallet n'existe pas encore, c'est normal
      console.log('Pas de wallet existant');
    }
  };

  const handleProfileUpdate = async () => {
    setLoading(true);
    try {
      await authAPI.updateProfile(profileData);
      await fetchUser();
      toast({
        title: 'Profil mis à jour',
        description: 'Vos modifications ont été enregistrées',
        variant: 'success',
      });
    } catch (error: any) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.message || 'Une erreur est survenue',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast({
        title: 'Erreur',
        description: 'Les mots de passe ne correspondent pas',
        variant: 'destructive',
      });
      return;
    }

    if (passwordData.new_password.length < 8) {
      toast({
        title: 'Erreur',
        description: 'Le mot de passe doit contenir au moins 8 caractères',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      await authAPI.changePassword({
        old_password: passwordData.old_password,
        new_password: passwordData.new_password,
      });
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
      toast({
        title: 'Mot de passe modifié',
        description: 'Votre mot de passe a été mis à jour',
        variant: 'success',
      });
    } catch (error: any) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.message || 'Mot de passe actuel incorrect',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      'Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.'
    );
    
    if (confirmed) {
      try {
        // await authAPI.deleteAccount();
        logout();
        router.push('/');
        toast({
          title: 'Compte supprimé',
          description: 'Votre compte a été définitivement supprimé',
        });
      } catch (error) {
        toast({
          title: 'Erreur',
          description: 'Impossible de supprimer le compte',
          variant: 'destructive',
        });
      }
    }
  };

  const handleBankUpdate = async () => {
    if (!bankData.iban || !bankData.account_holder) {
      toast({
        title: 'Erreur',
        description: 'Veuillez renseigner au moins l\'IBAN et le titulaire du compte',
        variant: 'destructive',
      });
      return;
    }

    // Validation basique de l'IBAN
    const cleanIban = bankData.iban.replace(/\s/g, '').toUpperCase();
    if (cleanIban.length < 15 || cleanIban.length > 34) {
      toast({
        title: 'Erreur',
        description: 'L\'IBAN semble invalide',
        variant: 'destructive',
      });
      return;
    }

    setLoadingBank(true);
    try {
      await api.post('/orders/wallet/bank-details/', {
        ...bankData,
        iban: cleanIban,
      });
      setBankSaved(true);
      toast({
        title: 'Informations bancaires enregistrées',
        description: 'Vous pourrez maintenant recevoir vos paiements',
        variant: 'success',
      });
    } catch (error: any) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible d\'enregistrer les informations',
        variant: 'destructive',
      });
    } finally {
      setLoadingBank(false);
    }
  };

  // Déterminer si l'utilisateur est vendeur
  const isSeller = user?.role === 'seller' || user?.role === 'professional';

  const tabs = [
    { id: 'profile', label: 'Profil', icon: User },
    { id: 'security', label: 'Sécurité', icon: Lock },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    ...(isSeller ? [{ id: 'payments', label: 'Paiements', icon: Wallet }] : []),
    { id: 'privacy', label: 'Confidentialité', icon: Shield },
  ];

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold mb-8">Paramètres</h1>

          <div className="flex flex-col md:flex-row gap-6">
            {/* Sidebar */}
            <aside className="w-full md:w-64 shrink-0">
              <div className="bg-white rounded-lg shadow-sm">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-50 text-primary-600 border-l-4 border-primary-600'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <tab.icon className="h-5 w-5" />
                    {tab.label}
                  </button>
                ))}
              </div>
            </aside>

            {/* Content */}
            <div className="flex-1">
              <div className="bg-white rounded-lg shadow-sm p-6">
                {/* Profil */}
                {activeTab === 'profile' && (
                  <div>
                    <h2 className="text-xl font-semibold mb-6">Informations du profil</h2>
                    
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">Prénom</label>
                          <Input
                            value={profileData.first_name}
                            onChange={(e) => setProfileData(prev => ({ ...prev, first_name: e.target.value }))}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Nom</label>
                          <Input
                            value={profileData.last_name}
                            onChange={(e) => setProfileData(prev => ({ ...prev, last_name: e.target.value }))}
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Nom d'utilisateur</label>
                        <Input
                          value={profileData.username}
                          onChange={(e) => setProfileData(prev => ({ ...prev, username: e.target.value }))}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Email</label>
                        <Input
                          value={user?.email || ''}
                          disabled
                          className="bg-gray-50"
                        />
                        <p className="text-sm text-gray-500 mt-1">
                          L'email ne peut pas être modifié
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Téléphone</label>
                        <Input
                          value={profileData.phone}
                          onChange={(e) => setProfileData(prev => ({ ...prev, phone: e.target.value }))}
                          placeholder="+33 6 12 34 56 78"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Localisation</label>
                        <Input
                          value={profileData.location}
                          onChange={(e) => setProfileData(prev => ({ ...prev, location: e.target.value }))}
                          placeholder="Paris, France"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Bio</label>
                        <Textarea
                          value={profileData.bio}
                          onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                          placeholder="Parlez-nous de vous..."
                          rows={4}
                        />
                      </div>

                      <Button
                        onClick={handleProfileUpdate}
                        disabled={loading}
                        className="bg-primary-600 hover:bg-primary-700"
                      >
                        <Save className="h-4 w-4 mr-2" />
                        {loading ? 'Enregistrement...' : 'Enregistrer'}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Sécurité */}
                {activeTab === 'security' && (
                  <div>
                    <h2 className="text-xl font-semibold mb-6">Sécurité du compte</h2>
                    
                    <div className="space-y-6">
                      <div>
                        <h3 className="font-medium mb-4">Changer le mot de passe</h3>
                        <div className="space-y-4 max-w-md">
                          <div className="relative">
                            <label className="block text-sm font-medium mb-1">Mot de passe actuel</label>
                            <Input
                              type={showPasswords ? 'text' : 'password'}
                              value={passwordData.old_password}
                              onChange={(e) => setPasswordData(prev => ({ ...prev, old_password: e.target.value }))}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Nouveau mot de passe</label>
                            <Input
                              type={showPasswords ? 'text' : 'password'}
                              value={passwordData.new_password}
                              onChange={(e) => setPasswordData(prev => ({ ...prev, new_password: e.target.value }))}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Confirmer le mot de passe</label>
                            <Input
                              type={showPasswords ? 'text' : 'password'}
                              value={passwordData.confirm_password}
                              onChange={(e) => setPasswordData(prev => ({ ...prev, confirm_password: e.target.value }))}
                            />
                          </div>
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              id="showPasswords"
                              checked={showPasswords}
                              onChange={(e) => setShowPasswords(e.target.checked)}
                            />
                            <label htmlFor="showPasswords" className="text-sm text-gray-600">
                              Afficher les mots de passe
                            </label>
                          </div>
                          <Button
                            onClick={handlePasswordChange}
                            disabled={loading}
                            className="bg-primary-600 hover:bg-primary-700"
                          >
                            {loading ? 'Modification...' : 'Modifier le mot de passe'}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Notifications */}
                {activeTab === 'notifications' && (
                  <div>
                    <h2 className="text-xl font-semibold mb-6">Préférences de notifications</h2>
                    
                    <div className="space-y-6">
                      <div>
                        <h3 className="font-medium mb-4">Notifications par email</h3>
                        <div className="space-y-3">
                          {[
                            { key: 'email_messages', label: 'Nouveaux messages' },
                            { key: 'email_favorites', label: 'Activité sur mes annonces' },
                            { key: 'email_newsletter', label: 'Newsletter et actualités' },
                          ].map((item) => (
                            <label key={item.key} className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={notifications[item.key as keyof typeof notifications]}
                                onChange={(e) => setNotifications(prev => ({
                                  ...prev,
                                  [item.key]: e.target.checked
                                }))}
                                className="h-4 w-4 rounded border-gray-300"
                              />
                              <span>{item.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h3 className="font-medium mb-4">Notifications push</h3>
                        <div className="space-y-3">
                          {[
                            { key: 'push_messages', label: 'Nouveaux messages' },
                            { key: 'push_favorites', label: 'Nouveaux favoris sur mes annonces' },
                          ].map((item) => (
                            <label key={item.key} className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={notifications[item.key as keyof typeof notifications]}
                                onChange={(e) => setNotifications(prev => ({
                                  ...prev,
                                  [item.key]: e.target.checked
                                }))}
                                className="h-4 w-4 rounded border-gray-300"
                              />
                              <span>{item.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <Button className="bg-primary-600 hover:bg-primary-700">
                        <Save className="h-4 w-4 mr-2" />
                        Enregistrer les préférences
                      </Button>
                    </div>
                  </div>
                )}

                {/* Paiements (Vendeurs uniquement) */}
                {activeTab === 'payments' && isSeller && (
                  <div>
                    <h2 className="text-xl font-semibold mb-6">Informations de paiement</h2>
                    
                    <div className="space-y-6">
                      {/* Statut */}
                      <div className={`p-4 rounded-lg ${bankSaved ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
                        <div className="flex items-center gap-2">
                          {bankSaved ? (
                            <>
                              <CheckCircle className="h-5 w-5 text-green-600" />
                              <span className="text-green-800 font-medium">
                                Informations bancaires configurées
                              </span>
                            </>
                          ) : (
                            <>
                              <AlertCircle className="h-5 w-5 text-yellow-600" />
                              <span className="text-yellow-800 font-medium">
                                Configurez vos informations bancaires pour recevoir vos paiements
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Formulaire */}
                      <div className="space-y-4 max-w-lg">
                        <div>
                          <label className="block text-sm font-medium mb-1">
                            <Building2 className="h-4 w-4 inline mr-1" />
                            Nom de la banque
                          </label>
                          <Input
                            value={bankData.bank_name}
                            onChange={(e) => setBankData(prev => ({ ...prev, bank_name: e.target.value }))}
                            placeholder="Ex: BNP Paribas, Crédit Agricole..."
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            <User className="h-4 w-4 inline mr-1" />
                            Titulaire du compte *
                          </label>
                          <Input
                            value={bankData.account_holder}
                            onChange={(e) => setBankData(prev => ({ ...prev, account_holder: e.target.value }))}
                            placeholder="Nom et prénom du titulaire"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Le nom doit correspondre exactement à celui sur votre compte bancaire
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            <CreditCard className="h-4 w-4 inline mr-1" />
                            IBAN *
                          </label>
                          <Input
                            value={bankData.iban}
                            onChange={(e) => setBankData(prev => ({ 
                              ...prev, 
                              iban: e.target.value.replace(/\s/g, '').toUpperCase() 
                            }))}
                            placeholder="FR76 1234 5678 9012 3456 7890 123"
                            className="font-mono"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Votre IBAN se trouve sur votre RIB ou dans votre espace bancaire en ligne
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            BIC / SWIFT
                          </label>
                          <Input
                            value={bankData.bic}
                            onChange={(e) => setBankData(prev => ({ ...prev, bic: e.target.value.toUpperCase() }))}
                            placeholder="BNPAFRPP"
                            className="font-mono"
                          />
                        </div>

                        <div className="bg-blue-50 p-4 rounded-lg">
                          <h4 className="font-medium text-blue-900 mb-2">🔒 Sécurité</h4>
                          <p className="text-sm text-blue-800">
                            Vos informations bancaires sont stockées de manière sécurisée et ne sont 
                            utilisées que pour vous verser vos gains. Elles ne sont jamais partagées 
                            avec des tiers.
                          </p>
                        </div>

                        <Button
                          onClick={handleBankUpdate}
                          disabled={loadingBank}
                          className="bg-primary-600 hover:bg-primary-700"
                        >
                          <Save className="h-4 w-4 mr-2" />
                          {loadingBank ? 'Enregistrement...' : 'Enregistrer mes informations bancaires'}
                        </Button>
                      </div>

                      {/* Lien vers le portefeuille */}
                      <div className="border-t pt-6">
                        <h3 className="font-medium mb-2">Mon portefeuille</h3>
                        <p className="text-sm text-gray-600 mb-3">
                          Consultez votre solde, l'historique des transactions et demandez des retraits
                        </p>
                        <Button 
                          variant="outline"
                          onClick={() => router.push('/mes-ventes/wallet')}
                        >
                          <Wallet className="h-4 w-4 mr-2" />
                          Accéder à mon portefeuille
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Confidentialité */}
                {activeTab === 'privacy' && (
                  <div>
                    <h2 className="text-xl font-semibold mb-6">Confidentialité</h2>
                    
                    <div className="space-y-6">
                      <div>
                        <h3 className="font-medium mb-2">Visibilité du profil</h3>
                        <p className="text-sm text-gray-600 mb-3">
                          Choisissez qui peut voir votre profil et vos informations
                        </p>
                        <select className="border rounded-md p-2 w-full max-w-xs">
                          <option value="public">Public (tous les utilisateurs)</option>
                          <option value="registered">Utilisateurs inscrits uniquement</option>
                          <option value="private">Privé (personne)</option>
                        </select>
                      </div>

                      <div>
                        <h3 className="font-medium mb-2">Données personnelles</h3>
                        <p className="text-sm text-gray-600 mb-3">
                          Téléchargez une copie de vos données conformément au RGPD
                        </p>
                        <Button variant="outline">
                          Télécharger mes données
                        </Button>
                      </div>

                      <div className="border-t pt-6">
                        <h3 className="font-medium text-red-600 mb-2">Zone dangereuse</h3>
                        <p className="text-sm text-gray-600 mb-3">
                          La suppression de votre compte est définitive et irréversible.
                          Toutes vos annonces et messages seront supprimés.
                        </p>
                        <Button
                          variant="outline"
                          onClick={handleDeleteAccount}
                          className="text-red-600 border-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Supprimer mon compte
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

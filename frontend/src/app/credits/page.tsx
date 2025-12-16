'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { paymentsAPI } from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import {
  Coins,
  Check,
  CreditCard,
  Zap,
  ShieldCheck,
  Clock,
  Star,
  Loader2,
} from 'lucide-react';

interface CreditPack {
  id: number;
  name: string;
  slug: string;
  credits: number;
  bonus_credits: number;
  price: string;
  description: string;
  is_popular: boolean;
  total_credits: number;
  price_per_credit: number;
}

export default function CreditsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [creditPacks, setCreditPacks] = useState<CreditPack[]>([]);
  const [selectedPack, setSelectedPack] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [userCredits, setUserCredits] = useState<number>(0);

  useEffect(() => {
    fetchCreditPacks();
    if (isAuthenticated) {
      fetchUserCredits();
    }
  }, [isAuthenticated]);

  const fetchCreditPacks = async () => {
    try {
      const response = await paymentsAPI.getCreditPacks();
      // Handle both array and paginated response
      const packs = Array.isArray(response.data) 
        ? response.data 
        : response.data?.results || [];
      setCreditPacks(packs);
      // Sélectionner le pack populaire par défaut
      const popularPack = packs.find((p: CreditPack) => p.is_popular);
      if (popularPack) {
        setSelectedPack(popularPack.id);
      } else if (packs.length > 0) {
        setSelectedPack(packs[0].id);
      }
    } catch (error) {
      console.error('Error fetching credit packs:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les packs de crédits',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserCredits = async () => {
    try {
      const response = await paymentsAPI.getCredits();
      setUserCredits(response.data.balance);
    } catch (error) {
      console.error('Error fetching user credits:', error);
    }
  };

  const handlePurchase = async () => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/credits');
      return;
    }

    if (!selectedPack) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un pack de crédits',
        variant: 'destructive',
      });
      return;
    }

    setIsProcessing(true);
    try {
      const response = await paymentsAPI.createCreditSession(selectedPack);
      
      if (response.data.checkout_url) {
        // Rediriger vers Stripe Checkout
        window.location.href = response.data.checkout_url;
      } else {
        toast({
          title: 'Erreur',
          description: 'Impossible de créer la session de paiement',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      console.error('Error creating checkout session:', error);
      toast({
        title: 'Erreur',
        description: error.response?.data?.error || 'Une erreur est survenue lors du paiement',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const selectedPackData = creditPacks.find(p => p.id === selectedPack);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-12">
        <div className="container mx-auto px-4 max-w-5xl">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full mb-4">
              <Coins className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Crédits de publication
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Achetez des crédits pour publier vos annonces à l'unité, 
              sans engagement mensuel.
            </p>
          </div>

          {/* Current balance if authenticated */}
          {isAuthenticated && (
            <div className="bg-white rounded-xl shadow-sm p-6 mb-8 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                  <Coins className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Votre solde actuel</p>
                  <p className="text-2xl font-bold text-gray-900">{userCredits} crédit{userCredits !== 1 ? 's' : ''}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">1 crédit = 1 annonce</p>
              </div>
            </div>
          )}

          {/* Loading state */}
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
          ) : (
            <>
              {/* Credit Packs */}
              <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4 mb-12">
                {creditPacks.map((pack) => (
                  <div
                    key={pack.id}
                    onClick={() => setSelectedPack(pack.id)}
                    className={`relative rounded-xl border-2 p-6 cursor-pointer transition-all ${
                      selectedPack === pack.id
                        ? 'border-primary-500 bg-primary-50 shadow-lg scale-105'
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                    }`}
                  >
                    {pack.is_popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                          Populaire
                        </span>
                      </div>
                    )}

                    <div className="text-center">
                      <div className="text-3xl font-bold text-gray-900 mb-1">
                        {pack.credits}
                      </div>
                      <div className="text-sm text-gray-500 mb-4">
                        crédit{pack.credits > 1 ? 's' : ''}
                        {pack.bonus_credits > 0 && (
                          <span className="block text-green-600 font-semibold">
                            +{pack.bonus_credits} bonus
                          </span>
                        )}
                      </div>

                      <div className="text-2xl font-bold text-primary-600 mb-1">
                        {parseFloat(pack.price).toFixed(2)} €
                      </div>
                      <div className="text-xs text-gray-400">
                        {(parseFloat(pack.price) / pack.total_credits).toFixed(2)} €/crédit
                      </div>

                      {selectedPack === pack.id && (
                        <div className="mt-4">
                          <Check className="w-6 h-6 text-primary-600 mx-auto" />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Purchase Button */}
              <div className="text-center mb-12">
                <Button
                  variant="gradient"
                  size="lg"
                  onClick={handlePurchase}
                  loading={isProcessing}
                  disabled={!selectedPack || isProcessing}
                  className="px-12"
                >
                  <CreditCard className="w-5 h-5 mr-2" />
                  {selectedPackData 
                    ? `Acheter ${selectedPackData.total_credits} crédits pour ${parseFloat(selectedPackData.price).toFixed(2)} €`
                    : 'Sélectionnez un pack'}
                </Button>
                <p className="text-sm text-gray-500 mt-4">
                  Paiement sécurisé par Stripe
                </p>
              </div>
            </>
          )}

          {/* Features */}
          <div className="bg-white rounded-xl shadow-sm p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">
              Pourquoi acheter des crédits ?
            </h2>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Zap className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Flexibilité</h3>
                <p className="text-sm text-gray-500">
                  Publiez quand vous voulez, sans abonnement
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <ShieldCheck className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Sans expiration</h3>
                <p className="text-sm text-gray-500">
                  Vos crédits n'expirent jamais
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Clock className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Utilisation immédiate</h3>
                <p className="text-sm text-gray-500">
                  Crédités instantanément sur votre compte
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Star className="w-6 h-6 text-amber-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Économies</h3>
                <p className="text-sm text-gray-500">
                  Plus vous achetez, moins c'est cher
                </p>
              </div>
            </div>
          </div>

          {/* Comparison with subscription */}
          <div className="mt-8 text-center">
            <p className="text-gray-600 mb-4">
              Vous publiez régulièrement ? Un abonnement pourrait vous convenir !
            </p>
            <Button
              variant="outline"
              onClick={() => router.push('/abonnements')}
            >
              Voir les abonnements
            </Button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

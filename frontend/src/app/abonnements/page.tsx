'use client';

import { useState, useEffect } from 'react';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { paymentsAPI } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { useRouter } from 'next/navigation';
import { toast } from '@/hooks/use-toast';
import {
  Check,
  Star,
  Zap,
  Shield,
  TrendingUp,
  Users,
  Package,
  Crown,
  Loader2,
  Building,
} from 'lucide-react';

interface SubscriptionPlan {
  id: number;
  name: string;
  slug: string;
  plan_type: string;
  billing_cycle: string;
  price: string;
  max_listings: number;
  max_images_per_listing: number;
  can_boost: boolean;
  boost_count_per_month: number;
  featured_badge: boolean;
  priority_support: boolean;
  analytics_access: boolean;
  description: string;
  features_list: string[];
  is_popular: boolean;
}

const getIconForPlan = (planType: string) => {
  switch (planType) {
    case 'basic':
      return <Star className="h-8 w-8" />;
    case 'pro':
      return <Crown className="h-8 w-8" />;
    case 'business':
      return <Building className="h-8 w-8" />;
    default:
      return <Package className="h-8 w-8" />;
  }
};

const getColorForPlan = (planType: string) => {
  switch (planType) {
    case 'basic':
      return 'bg-blue-100 text-blue-600';
    case 'pro':
      return 'bg-primary-100 text-primary-600';
    case 'business':
      return 'bg-purple-100 text-purple-600';
    default:
      return 'bg-gray-100 text-gray-600';
  }
};

export default function SubscriptionsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState<number | null>(null);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [isLoadingPlans, setIsLoadingPlans] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await paymentsAPI.getPlans();
      // Handle both array and paginated response
      const plansData = Array.isArray(response.data) 
        ? response.data 
        : response.data?.results || [];
      setPlans(plansData);
    } catch (error) {
      console.error('Error fetching plans:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les plans',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingPlans(false);
    }
  };

  const handleSubscribe = async (planId: number) => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/abonnements');
      return;
    }

    setLoading(planId);
    try {
      const response = await paymentsAPI.createSubscriptionSession(planId);
      // Redirect to Stripe Checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        toast({
          title: 'Erreur',
          description: 'Impossible de créer la session de paiement',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      console.error('Subscription error:', error);
      toast({
        title: 'Erreur',
        description: error.response?.data?.error || error.response?.data?.message || 'Une erreur est survenue',
        variant: 'destructive',
      });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-12">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Choisissez votre plan
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Développez votre activité avec nos offres adaptées à vos besoins.
              Publiez plus d'annonces et boostez votre visibilité.
            </p>
          </div>

          {/* Loading state */}
          {isLoadingPlans ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            </div>
          ) : (
            <>
              {/* Plans */}
              <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                {plans.map((plan) => (
                  <div
                    key={plan.id}
                    className={`relative bg-white rounded-2xl shadow-lg overflow-hidden ${
                      plan.is_popular ? 'ring-2 ring-primary-600' : ''
                    }`}
                  >
                    {plan.is_popular && (
                      <div className="absolute top-0 left-0 right-0 bg-primary-600 text-white text-center py-1 text-sm font-medium">
                        Le plus populaire
                      </div>
                    )}
                    <div className={`p-8 ${plan.is_popular ? 'pt-12' : ''}`}>
                      <div className={`inline-flex p-3 rounded-lg mb-4 ${getColorForPlan(plan.plan_type)}`}>
                        {getIconForPlan(plan.plan_type)}
                      </div>
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                      <p className="text-gray-500 text-sm mb-4">{plan.description}</p>
                      <div className="mb-6">
                        <span className="text-4xl font-bold text-gray-900">
                          {parseFloat(plan.price).toFixed(2)}€
                        </span>
                        <span className="text-gray-500">
                          /{plan.billing_cycle === 'monthly' ? 'mois' : 'an'}
                        </span>
                      </div>

                      <ul className="space-y-3 mb-8">
                        {(plan.features_list || []).map((feature, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <Check className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                            <span className="text-gray-600">{feature}</span>
                          </li>
                        ))}
                      </ul>

                      <Button
                        onClick={() => handleSubscribe(plan.id)}
                        disabled={loading !== null}
                        className={`w-full ${
                          plan.is_popular
                            ? 'bg-primary-600 hover:bg-primary-700'
                            : 'bg-gray-900 hover:bg-gray-800'
                        }`}
                      >
                        {loading === plan.id ? (
                          <span className="flex items-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Chargement...
                          </span>
                        ) : (
                          'Souscrire'
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Features comparison */}
          <div className="mt-16 max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-center mb-8">
              Pourquoi choisir un abonnement ?
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="inline-flex p-4 bg-primary-100 rounded-full mb-4">
                  <TrendingUp className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Plus de visibilité</h3>
                <p className="text-gray-600">
                  Vos annonces sont mises en avant et atteignent plus d'acheteurs
                </p>
              </div>
              <div className="text-center">
                <div className="inline-flex p-4 bg-primary-100 rounded-full mb-4">
                  <Shield className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Badge de confiance</h3>
                <p className="text-gray-600">
                  Inspirez confiance aux acheteurs avec votre badge vérifié
                </p>
              </div>
              <div className="text-center">
                <div className="inline-flex p-4 bg-primary-100 rounded-full mb-4">
                  <Users className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Support prioritaire</h3>
                <p className="text-gray-600">
                  Notre équipe est à votre disposition pour vous aider
                </p>
              </div>
            </div>
          </div>

          {/* Pay per post option */}
          <div className="mt-16 max-w-2xl mx-auto bg-white rounded-2xl shadow-lg p-8 text-center">
            <Zap className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Pas besoin d'abonnement ?</h2>
            <p className="text-gray-600 mb-6">
              Achetez des crédits pour publier des annonces à l'unité.
              Idéal pour les vendeurs occasionnels.
            </p>
            <Button
              variant="outline"
              onClick={() => router.push('/credits')}
              className="px-8"
            >
              Acheter des crédits
            </Button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { CheckCircle, Coins, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import api from '@/lib/api';

function PaymentSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const paymentType = searchParams.get('type');
  const [isLoading, setIsLoading] = useState(true);
  const [confirmResult, setConfirmResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const confirmPayment = async () => {
      if (!sessionId) {
        setIsLoading(false);
        return;
      }

      try {
        // Appeler l'API de confirmation (simule le webhook en dev)
        const response = await api.post('/payments/dev-confirm/', {
          session_id: sessionId
        });
        setConfirmResult(response.data);
        console.log('Payment confirmed:', response.data);
      } catch (err: any) {
        // En production, le webhook gère cela, donc on ignore l'erreur
        console.log('Dev confirm response:', err.response?.data);
        if (err.response?.status === 404) {
          // Paiement déjà traité ou non trouvé - c'est OK
          setConfirmResult({ status: 'already_processed' });
        } else if (err.response?.status === 403) {
          // En production, pas de dev-confirm - normal
          setConfirmResult({ status: 'production_mode' });
        } else {
          setError(err.response?.data?.error || 'Erreur de confirmation');
        }
      } finally {
        setIsLoading(false);
      }
    };

    // Petit délai pour laisser la redirection se faire proprement
    const timer = setTimeout(confirmPayment, 1000);
    return () => clearTimeout(timer);
  }, [sessionId]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 flex items-center justify-center py-12">
        <div className="container mx-auto px-4 max-w-lg">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            {isLoading ? (
              <>
                <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 mb-4">
                  Traitement en cours...
                </h1>
                <p className="text-gray-600 mb-8">
                  Nous confirmons votre paiement, veuillez patienter.
                </p>
              </>
            ) : error ? (
              <>
                <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <AlertCircle className="w-10 h-10 text-red-600" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 mb-4">
                  Problème de confirmation
                </h1>
                <p className="text-gray-600 mb-8">
                  {error}. Veuillez contacter le support si le problème persiste.
                </p>
                <Link href="/dashboard" className="block">
                  <Button variant="outline" className="w-full">
                    Retour au tableau de bord
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <CheckCircle className="w-10 h-10 text-green-600" />
                </div>
                
                <h1 className="text-2xl font-bold text-gray-900 mb-4">
                  Paiement réussi !
                </h1>
                
                <p className="text-gray-600 mb-4">
                  {paymentType === 'credits' 
                    ? 'Vos crédits ont été ajoutés à votre compte. Vous pouvez maintenant publier vos annonces !'
                    : 'Votre abonnement est maintenant actif. Profitez de tous les avantages !'}
                </p>

                {confirmResult?.credits_added && (
                  <div className="bg-amber-50 rounded-xl p-4 mb-6 flex items-center justify-center gap-3">
                    <Coins className="w-6 h-6 text-amber-600" />
                    <span className="text-amber-800 font-medium">
                      +{confirmResult.credits_added} crédits ajoutés (solde: {confirmResult.new_balance})
                    </span>
                  </div>
                )}

                {confirmResult?.subscription_activated && (
                  <div className="bg-green-50 rounded-xl p-4 mb-6 flex items-center justify-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <span className="text-green-800 font-medium">
                      Abonnement {confirmResult.plan} activé !
                    </span>
                  </div>
                )}

                <div className="space-y-3">
                  <Link href="/annonces/nouvelle" className="block">
                    <Button variant="gradient" className="w-full">
                      Créer une annonce
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                  
                  <Link href="/dashboard" className="block">
                    <Button variant="outline" className="w-full">
                      Retour au tableau de bord
                    </Button>
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    }>
      <PaymentSuccessContent />
    </Suspense>
  );
}

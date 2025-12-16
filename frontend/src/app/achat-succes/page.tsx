'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { CheckCircle, Package, MessageSquare, Loader2, AlertCircle, Bell } from 'lucide-react';
import api from '@/lib/api';

function PurchaseSuccessContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const listingSlug = searchParams.get('listing');
  const [isLoading, setIsLoading] = useState(true);
  const [purchaseInfo, setPurchaseInfo] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const confirmPurchase = async () => {
      if (!sessionId) {
        setIsLoading(false);
        return;
      }

      try {
        // Appeler l'API de confirmation (simule le webhook en dev)
        const response = await api.post('/payments/dev-confirm/', {
          session_id: sessionId
        });
        setPurchaseInfo(response.data);
        console.log('Purchase confirmed:', response.data);
      } catch (err: any) {
        console.log('Dev confirm response:', err.response?.data);
        if (err.response?.status === 404) {
          setPurchaseInfo({ status: 'already_processed' });
        } else if (err.response?.status === 403) {
          setPurchaseInfo({ status: 'production_mode' });
        } else {
          setError(err.response?.data?.error || 'Erreur de confirmation');
        }
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(confirmPurchase, 1000);
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
                  Traitement de votre achat...
                </h1>
                <p className="text-gray-600 mb-8">
                  Veuillez patienter pendant que nous confirmons votre paiement.
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
                  Achat confirmé ! 🎉
                </h1>
                
                <p className="text-gray-600 mb-6">
                  Votre paiement a été effectué avec succès. Le vendeur a été notifié de votre achat.
                </p>

                <div className="bg-green-50 rounded-xl p-4 mb-6">
                  <div className="flex items-center justify-center gap-3">
                    <Package className="w-6 h-6 text-green-600" />
                    <span className="text-green-800 font-medium">
                      Transaction enregistrée
                    </span>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-xl p-4 mb-6">
                  <h3 className="font-semibold text-blue-800 mb-2">Prochaines étapes</h3>
                  <ul className="text-sm text-blue-700 text-left space-y-2">
                    <li>• Contactez le vendeur pour organiser la remise</li>
                    <li>• Privilégiez les lieux publics pour la rencontre</li>
                    <li>• Vérifiez l'article avant de finaliser</li>
                  </ul>
                </div>

                <div className="space-y-3">
                  <Link href="/messages" className="block">
                    <Button variant="gradient" className="w-full">
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Contacter le vendeur
                    </Button>
                  </Link>
                  
                  <Link href="/notifications" className="block">
                    <Button variant="outline" className="w-full">
                      <Bell className="w-4 h-4 mr-2" />
                      Voir mes notifications
                    </Button>
                  </Link>
                  
                  {listingSlug && (
                    <Link href={`/annonces/${listingSlug}`} className="block">
                      <Button variant="outline" className="w-full">
                        Voir l'annonce
                      </Button>
                    </Link>
                  )}
                  
                  <Link href="/dashboard" className="block">
                    <Button variant="ghost" className="w-full">
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

export default function PurchaseSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    }>
      <PurchaseSuccessContent />
    </Suspense>
  );
}

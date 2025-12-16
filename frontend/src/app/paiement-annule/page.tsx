'use client';

import Link from 'next/link';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { XCircle, ArrowLeft, RotateCcw } from 'lucide-react';

export default function PaymentCancelPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 flex items-center justify-center py-12">
        <div className="container mx-auto px-4 max-w-lg">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-red-600" />
            </div>
            
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Paiement annulé
            </h1>
            
            <p className="text-gray-600 mb-8">
              Votre paiement a été annulé. Aucun montant n'a été débité de votre compte.
              Vous pouvez réessayer à tout moment.
            </p>

            <div className="space-y-3">
              <Link href="/credits" className="block">
                <Button variant="gradient" className="w-full">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Réessayer
                </Button>
              </Link>
              
              <Link href="/dashboard" className="block">
                <Button variant="outline" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Retour au tableau de bord
                </Button>
              </Link>
            </div>

            <p className="text-sm text-gray-500 mt-8">
              Besoin d'aide ? <Link href="/contact" className="text-primary-600 hover:underline">Contactez-nous</Link>
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

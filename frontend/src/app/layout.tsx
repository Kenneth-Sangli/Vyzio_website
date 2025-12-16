import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Toaster } from '@/components/ui/toaster';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Vyzio - Marketplace d\'annonces',
  description: 'Achetez et vendez facilement des produits, services et prestations sur Vyzio',
  keywords: ['marketplace', 'annonces', 'vente', 'achat', 'occasion', 'services'],
  authors: [{ name: 'Vyzio Team' }],
  openGraph: {
    title: 'Vyzio - Marketplace d\'annonces',
    description: 'Achetez et vendez facilement des produits, services et prestations',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}

'use client';

// Cette page redirige vers /annonces/nouvelle
// C'est un alias pour la compatibilité des liens

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function CreateListingRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/annonces/nouvelle');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
    </div>
  );
}

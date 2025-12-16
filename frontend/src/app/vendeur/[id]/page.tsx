'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { listingsAPI, reviewsAPI, messagesAPI, type Listing, type Review, type User } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from '@/hooks/use-toast';
import Link from 'next/link';
import {
  MapPin,
  Star,
  Calendar,
  MessageCircle,
  Shield,
  Package,
  Clock,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SellerProfile {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
  bio: string;
  location: string;
  role: string;
  is_verified: boolean;
  avg_rating: number;
  total_reviews: number;
  created_at: string;
  listings_count?: number;
}

export default function SellerProfilePage() {
  const params = useParams();
  const sellerId = params.id as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  
  const [seller, setSeller] = useState<SellerProfile | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'listings' | 'reviews'>('listings');
  
  // Modal pour contacter le vendeur
  const [showContactModal, setShowContactModal] = useState(false);
  const [contactMessage, setContactMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);

  useEffect(() => {
    if (sellerId) fetchSellerData();
  }, [sellerId]);

  const fetchSellerData = async () => {
    setLoading(true);
    try {
      // Récupérer le profil du vendeur via l'API users
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/users/${sellerId}/`);
      if (response.ok) {
        const sellerData = await response.json();
        setSeller(sellerData);
        
        // Récupérer les annonces du vendeur
        const listingsResponse = await listingsAPI.getAll({ seller: sellerId });
        setListings(listingsResponse.data.results);
        
        // Récupérer les avis
        try {
          const reviewsResponse = await reviewsAPI.getForUser(sellerId);
          setReviews(reviewsResponse.data.reviews || []);
        } catch (e) {
          console.error('Error fetching reviews:', e);
        }
      }
    } catch (error) {
      console.error('Error fetching seller data:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger le profil du vendeur',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleContact = async () => {
    if (!isAuthenticated) {
      toast({
        title: 'Connexion requise',
        description: 'Connectez-vous pour contacter ce vendeur',
        variant: 'destructive',
      });
      return;
    }

    if (!contactMessage.trim()) {
      toast({
        title: 'Message vide',
        description: 'Veuillez écrire un message',
        variant: 'destructive',
      });
      return;
    }

    setSendingMessage(true);
    try {
      // Utiliser seller.id et optionnellement la première annonce
      const listingId = listings.length > 0 ? listings[0].id : undefined;
      await messagesAPI.startConversation(seller!.id, listingId, contactMessage);
      toast({
        title: 'Message envoyé',
        description: 'Le vendeur recevra votre message',
        variant: 'success',
      });
      setShowContactModal(false);
      setContactMessage('');
    } catch (error: any) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.message || 'Impossible d\'envoyer le message',
        variant: 'destructive',
      });
    } finally {
      setSendingMessage(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!seller) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-2">Vendeur introuvable</h1>
            <p className="text-gray-600 mb-4">Ce profil n'existe pas ou a été supprimé</p>
            <Link href="/" className="text-primary-600 hover:underline">
              Retour à l'accueil
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4">
          {/* Profil header */}
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="flex flex-col md:flex-row gap-6">
              {/* Avatar */}
              <div className="shrink-0">
                {seller.avatar ? (
                  <img
                    src={seller.avatar}
                    alt={seller.username}
                    className="w-32 h-32 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-primary-100 flex items-center justify-center">
                    <span className="text-4xl font-bold text-primary-600">
                      {seller.first_name?.[0] || seller.username[0]}
                    </span>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h1 className="text-2xl font-bold">
                    {seller.first_name} {seller.last_name?.[0]}.
                  </h1>
                  {seller.is_verified && (
                    <Shield className="h-5 w-5 text-blue-500" />
                  )}
                  {seller.role === 'professional' && (
                    <span className="bg-primary-100 text-primary-700 text-xs px-2 py-1 rounded-full">
                      Pro
                    </span>
                  )}
                </div>

                <p className="text-gray-500 mb-4">@{seller.username}</p>

                {seller.bio && (
                  <p className="text-gray-700 mb-4">{seller.bio}</p>
                )}

                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                  {seller.location && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {seller.location}
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Membre depuis {formatDate(seller.created_at)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Package className="h-4 w-4" />
                    {listings.length} annonce{listings.length > 1 ? 's' : ''}
                  </div>
                </div>

                {/* Rating */}
                <div className="flex items-center gap-2 mt-4">
                  <div className="flex items-center">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`h-5 w-5 ${
                          star <= seller.avg_rating
                            ? 'text-yellow-400 fill-yellow-400'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="font-semibold">{parseFloat(String(seller.avg_rating || 0)).toFixed(1)}</span>
                  <span className="text-gray-500">({seller.total_reviews} avis)</span>
                </div>
              </div>

              {/* Actions */}
              <div className="shrink-0 flex flex-col gap-2">
                {currentUser?.id !== seller.id && (
                  <Button
                    onClick={() => setShowContactModal(true)}
                    className="bg-primary-600 hover:bg-primary-700"
                  >
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Contacter
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-xl shadow-sm mb-6">
            <div className="border-b">
              <div className="flex">
                <button
                  onClick={() => setActiveTab('listings')}
                  className={`px-6 py-4 font-medium ${
                    activeTab === 'listings'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Annonces ({listings.length})
                </button>
                <button
                  onClick={() => setActiveTab('reviews')}
                  className={`px-6 py-4 font-medium ${
                    activeTab === 'reviews'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Avis ({reviews.length})
                </button>
              </div>
            </div>

            <div className="p-6">
              {activeTab === 'listings' ? (
                listings.length === 0 ? (
                  <div className="text-center py-8">
                    <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Aucune annonce pour le moment</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {listings.map((listing) => (
                      <Link
                        key={listing.id}
                        href={`/annonces/${listing.slug || listing.id}`}
                        className="bg-gray-50 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                      >
                        <div className="aspect-[4/3]">
                          {listing.images?.[0] ? (
                            <img
                              src={listing.images[0].image}
                              alt={listing.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                              <span className="text-gray-400">Pas d'image</span>
                            </div>
                          )}
                        </div>
                        <div className="p-4">
                          <h3 className="font-semibold line-clamp-1">{listing.title}</h3>
                          <p className="text-primary-600 font-bold">{listing.price} €</p>
                        </div>
                      </Link>
                    ))}
                  </div>
                )
              ) : (
                reviews.length === 0 ? (
                  <div className="text-center py-8">
                    <Star className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Aucun avis pour le moment</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {reviews.map((review) => (
                      <div key={review.id} className="border-b pb-4 last:border-0">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="flex items-center">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <Star
                                key={star}
                                className={`h-4 w-4 ${
                                  star <= review.rating
                                    ? 'text-yellow-400 fill-yellow-400'
                                    : 'text-gray-300'
                                }`}
                              />
                            ))}
                          </div>
                          <span className="text-sm text-gray-500">
                            par {review.reviewer.username}
                          </span>
                          <span className="text-sm text-gray-400">
                            • {formatDate(review.created_at)}
                          </span>
                        </div>
                        <p className="text-gray-700">{review.comment}</p>
                        {review.seller_response && (
                          <div className="mt-2 pl-4 border-l-2 border-primary-200">
                            <p className="text-sm text-gray-600">
                              <span className="font-medium">Réponse du vendeur:</span>{' '}
                              {review.seller_response}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Modal contact */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold mb-4">
              Contacter {seller.first_name}
            </h2>
            <Textarea
              placeholder="Écrivez votre message..."
              value={contactMessage}
              onChange={(e) => setContactMessage(e.target.value)}
              className="mb-4"
              rows={4}
            />
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowContactModal(false)}
              >
                Annuler
              </Button>
              <Button
                onClick={handleContact}
                disabled={sendingMessage}
                className="bg-primary-600 hover:bg-primary-700"
              >
                {sendingMessage ? 'Envoi...' : 'Envoyer'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

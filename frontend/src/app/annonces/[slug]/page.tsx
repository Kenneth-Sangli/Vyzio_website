'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { listingsAPI, messagesAPI, paymentsAPI, type Listing } from '@/lib/api';
import { formatPrice, formatDate, formatRelativeTime } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from '@/hooks/use-toast';
import {
  Heart,
  Share2,
  MapPin,
  Clock,
  Eye,
  MessageSquare,
  Shield,
  ChevronLeft,
  ChevronRight,
  Star,
  Flag,
  User,
  Phone,
  Mail,
  Zap,
  CheckCircle,
  AlertTriangle,
  ShoppingCart,
  CreditCard,
  Loader2,
} from 'lucide-react';

export default function ListingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [listing, setListing] = useState<Listing | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [showContactForm, setShowContactForm] = useState(false);
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);

  useEffect(() => {
    fetchListing();
  }, [params.slug]);

  const fetchListing = async () => {
    try {
      const response = await listingsAPI.getBySlug(params.slug as string);
      setListing(response.data);
    } catch (error) {
      console.error('Error fetching listing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFavorite = async () => {
    if (!isAuthenticated) {
      toast({
        title: 'Connexion requise',
        description: 'Connectez-vous pour ajouter aux favoris',
        variant: 'destructive',
      });
      return;
    }
    try {
      await listingsAPI.toggleFavorite(listing!.id);
      setIsFavorite(!isFavorite);
      toast({
        title: isFavorite ? 'Retiré des favoris' : 'Ajouté aux favoris',
        variant: 'success',
      });
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const handlePurchase = async () => {
    if (!isAuthenticated) {
      toast({
        title: 'Connexion requise',
        description: 'Connectez-vous pour acheter cet article',
        variant: 'destructive',
      });
      router.push(`/connexion?redirect=/annonces/${params.slug}`);
      return;
    }

    // Vérifier que l'utilisateur est un acheteur (pas un vendeur)
    if (user?.role === 'seller') {
      toast({
        title: 'Action impossible',
        description: 'Les vendeurs ne peuvent pas acheter. Créez un compte acheteur.',
        variant: 'destructive',
      });
      return;
    }

    // Vérifier que ce n'est pas le vendeur
    if (user?.id === listing?.seller?.id) {
      toast({
        title: 'Action impossible',
        description: 'Vous ne pouvez pas acheter votre propre annonce',
        variant: 'destructive',
      });
      return;
    }

    setIsPurchasing(true);
    try {
      const response = await paymentsAPI.createPurchaseSession(listing!.id);
      
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
      console.error('Error creating purchase session:', error);
      toast({
        title: 'Erreur',
        description: error.response?.data?.error || 'Une erreur est survenue',
        variant: 'destructive',
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    setIsSending(true);
    try {
      // Envoyer seller_id et listing_id à l'API
      await messagesAPI.startConversation(listing!.seller.id, listing!.id, message);
      toast({
        title: 'Message envoyé',
        description: 'Le vendeur vous répondra bientôt',
        variant: 'success',
      });
      setMessage('');
      setShowContactForm(false);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible d\'envoyer le message',
        variant: 'destructive',
      });
    } finally {
      setIsSending(false);
    }
  };

  const nextImage = () => {
    if (listing?.images) {
      setCurrentImageIndex((prev) => (prev + 1) % listing.images.length);
    }
  };

  const prevImage = () => {
    if (listing?.images) {
      setCurrentImageIndex((prev) => (prev - 1 + listing.images.length) % listing.images.length);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Annonce introuvable</h1>
            <p className="text-gray-600 mb-4">Cette annonce n'existe plus ou a été supprimée.</p>
            <Link href="/annonces">
              <Button>Retour aux annonces</Button>
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const conditionLabels: Record<string, string> = {
    new: 'Neuf',
    like_new: 'Comme neuf',
    good: 'Bon état',
    fair: 'État correct',
    poor: 'Usé',
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1">
        <div className="container mx-auto px-4 py-8">
          {/* Breadcrumb */}
          <nav className="flex items-center text-sm text-gray-500 mb-6">
            <Link href="/" className="hover:text-primary-600">Accueil</Link>
            <span className="mx-2">/</span>
            <Link href="/annonces" className="hover:text-primary-600">Annonces</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900 truncate max-w-xs">{listing.title}</span>
          </nav>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Image Gallery */}
              <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
                <div className="relative aspect-[4/3]">
                  {listing.images?.length > 0 ? (
                    <>
                      <Image
                        src={listing.images[currentImageIndex].image}
                        alt={listing.title}
                        fill
                        className="object-cover"
                      />
                      {listing.images.length > 1 && (
                        <>
                          <button
                            onClick={prevImage}
                            className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-white/90 rounded-full shadow-lg hover:bg-white transition-colors"
                          >
                            <ChevronLeft className="h-6 w-6" />
                          </button>
                          <button
                            onClick={nextImage}
                            className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-white/90 rounded-full shadow-lg hover:bg-white transition-colors"
                          >
                            <ChevronRight className="h-6 w-6" />
                          </button>
                          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                            {listing.images.map((_, index) => (
                              <button
                                key={index}
                                onClick={() => setCurrentImageIndex(index)}
                                className={`w-2 h-2 rounded-full transition-colors ${
                                  index === currentImageIndex ? 'bg-white' : 'bg-white/50'
                                }`}
                              />
                            ))}
                          </div>
                        </>
                      )}
                    </>
                  ) : (
                    <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                      <span className="text-gray-400">Pas d'image</span>
                    </div>
                  )}

                  {/* Badges */}
                  <div className="absolute top-4 left-4 flex gap-2">
                    {listing.is_boosted && (
                      <span className="bg-yellow-500 text-white text-sm font-bold px-3 py-1 rounded-full flex items-center">
                        <Zap className="w-4 h-4 mr-1" />
                        Boost
                      </span>
                    )}
                  </div>
                </div>

                {/* Thumbnails */}
                {listing.images?.length > 1 && (
                  <div className="p-4 flex gap-2 overflow-x-auto">
                    {listing.images.map((image, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentImageIndex(index)}
                        className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                          index === currentImageIndex ? 'border-primary-500' : 'border-transparent'
                        }`}
                      >
                        <Image
                          src={image.image}
                          alt=""
                          width={80}
                          height={80}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Details */}
              <div className="bg-white rounded-2xl p-6 shadow-sm">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">{listing.title}</h1>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1" />
                        {listing.location}
                      </span>
                      <span className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {formatRelativeTime(listing.created_at)}
                      </span>
                      <span className="flex items-center">
                        <Eye className="h-4 w-4 mr-1" />
                        {listing.views_count} vues
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleFavorite}
                      className={`p-3 rounded-full border ${
                        isFavorite ? 'bg-red-50 border-red-200 text-red-500' : 'hover:bg-gray-50'
                      }`}
                    >
                      <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
                    </button>
                    <button className="p-3 rounded-full border hover:bg-gray-50">
                      <Share2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                <div className="flex items-baseline gap-3 mb-6">
                  <span className="text-3xl font-bold text-primary-600">{formatPrice(listing.price)}</span>
                  {listing.original_price && listing.original_price > listing.price && (
                    <span className="text-lg text-gray-400 line-through">{formatPrice(listing.original_price)}</span>
                  )}
                </div>

                {/* Info Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
                  <div>
                    <span className="text-sm text-gray-500">État</span>
                    <p className="font-medium">{conditionLabels[listing.condition] || listing.condition}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Type</span>
                    <p className="font-medium capitalize">{listing.listing_type}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Catégorie</span>
                    <p className="font-medium">{listing.category?.name}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Référence</span>
                    <p className="font-medium text-xs">{listing.id.slice(0, 8)}</p>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h2 className="text-lg font-semibold mb-3">Description</h2>
                  <p className="text-gray-700 whitespace-pre-line">{listing.description}</p>
                </div>
              </div>

              {/* Safety Tips */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
                <div className="flex items-start gap-4">
                  <AlertTriangle className="h-6 w-6 text-yellow-600 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-yellow-800 mb-2">Conseils de sécurité</h3>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      <li>• Ne payez jamais à l'avance sans avoir vu l'article</li>
                      <li>• Privilégiez les rencontres dans des lieux publics</li>
                      <li>• Méfiez-vous des offres trop alléchantes</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Seller Card */}
              <div className="bg-white rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
                    {listing.seller?.avatar ? (
                      <Image
                        src={listing.seller.avatar}
                        alt=""
                        width={64}
                        height={64}
                        className="w-16 h-16 rounded-full object-cover"
                      />
                    ) : (
                      <User className="h-8 w-8 text-primary-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {listing.seller?.first_name || listing.seller?.username}
                    </h3>
                    <div className="flex items-center text-sm text-gray-500">
                      <Star className="h-4 w-4 text-yellow-400 fill-current mr-1" />
                      <span>{listing.seller?.avg_rating || 'N/A'}</span>
                      <span className="mx-1">•</span>
                      <span>{listing.seller?.total_reviews || 0} avis</span>
                    </div>
                    {listing.seller?.is_verified && (
                      <span className="inline-flex items-center text-xs text-green-600 mt-1">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Vérifié
                      </span>
                    )}
                  </div>
                </div>

                <Link href={`/vendeur/${listing.seller?.id}`}>
                  <Button variant="outline" className="w-full mb-3">
                    Voir le profil
                  </Button>
                </Link>

                {showContactForm ? (
                  <div className="space-y-3">
                    <Textarea
                      placeholder="Bonjour, je suis intéressé par votre annonce..."
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      rows={4}
                    />
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => setShowContactForm(false)}
                      >
                        Annuler
                      </Button>
                      <Button
                        variant="gradient"
                        className="flex-1"
                        onClick={handleSendMessage}
                        loading={isSending}
                      >
                        Envoyer
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Bouton Acheter maintenant */}
                    {user?.id !== listing.seller?.id && (
                      <Button
                        variant="gradient"
                        className="w-full"
                        onClick={handlePurchase}
                        disabled={isPurchasing}
                      >
                        {isPurchasing ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <ShoppingCart className="h-4 w-4 mr-2" />
                        )}
                        Acheter maintenant - {formatPrice(listing.price)}
                      </Button>
                    )}
                    
                    {/* Bouton Contacter le vendeur */}
                    <Button
                      variant={user?.id !== listing.seller?.id ? "outline" : "gradient"}
                      className="w-full"
                      onClick={() => {
                        if (!isAuthenticated) {
                          toast({
                            title: 'Connexion requise',
                            description: 'Connectez-vous pour contacter le vendeur',
                            variant: 'destructive',
                          });
                          return;
                        }
                        setShowContactForm(true);
                      }}
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Contacter le vendeur
                    </Button>
                  </div>
                )}
              </div>

              {/* Trust & Safety */}
              <div className="bg-white rounded-2xl p-6 shadow-sm">
                <h3 className="font-semibold mb-4">Acheter en confiance</h3>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center text-gray-600">
                    <Shield className="h-5 w-5 text-green-500 mr-3" />
                    Messagerie sécurisée
                  </li>
                  <li className="flex items-center text-gray-600">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                    Profils vérifiés
                  </li>
                  <li className="flex items-center text-gray-600">
                    <Star className="h-5 w-5 text-green-500 mr-3" />
                    Système d'avis
                  </li>
                </ul>
              </div>

              {/* Report */}
              <button className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-red-500 transition-colors w-full py-3">
                <Flag className="h-4 w-4" />
                Signaler cette annonce
              </button>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

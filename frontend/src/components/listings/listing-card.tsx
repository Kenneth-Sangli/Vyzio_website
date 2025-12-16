import Link from 'next/link';
import Image from 'next/image';
import { Heart, MapPin, Eye, Clock, Zap } from 'lucide-react';
import { formatPrice, formatRelativeTime, truncate } from '@/lib/utils';
import type { Listing } from '@/lib/api';
import { cn } from '@/lib/utils';

interface ListingCardProps {
  listing: Listing;
  onFavorite?: (id: string) => void;
  isFavorite?: boolean;
  variant?: 'default' | 'compact' | 'horizontal';
}

export function ListingCard({ listing, onFavorite, isFavorite, variant = 'default' }: ListingCardProps) {
  const primaryImage = listing.images?.find((img) => img.is_primary) || listing.images?.[0];

  if (variant === 'horizontal') {
    return (
      <Link href={`/annonces/${listing.slug || listing.id}`}>
        <div className="card card-hover flex overflow-hidden">
          <div className="relative w-48 h-32 flex-shrink-0">
            {primaryImage ? (
              <Image
                src={primaryImage.image}
                alt={listing.title}
                fill
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                <span className="text-gray-400">Pas d'image</span>
              </div>
            )}
            {listing.is_boosted && (
              <div className="absolute top-2 left-2 bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded-full flex items-center">
                <Zap className="w-3 h-3 mr-1" />
                Boost
              </div>
            )}
          </div>
          <div className="flex-1 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">{listing.title}</h3>
            <p className="text-sm text-gray-500 mb-2">{truncate(listing.description, 80)}</p>
            <div className="flex items-center justify-between">
              <span className="text-lg font-bold text-primary-600">{formatPrice(listing.price)}</span>
              <span className="text-xs text-gray-400 flex items-center">
                <MapPin className="w-3 h-3 mr-1" />
                {listing.location}
              </span>
            </div>
          </div>
        </div>
      </Link>
    );
  }

  return (
    <div className="card card-hover group">
      {/* Image */}
      <Link href={`/annonces/${listing.slug || listing.id}`}>
        <div className="relative aspect-[4/3] overflow-hidden bg-gray-100">
          {primaryImage ? (
            <Image
              src={primaryImage.image}
              alt={listing.title}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-gray-400">Pas d'image</span>
            </div>
          )}
          
          {/* Badges */}
          <div className="absolute top-3 left-3 flex flex-col gap-2">
            {listing.is_boosted && (
              <span className="bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded-full flex items-center shadow-sm">
                <Zap className="w-3 h-3 mr-1" />
                Boost
              </span>
            )}
            {listing.status === 'sold' && (
              <span className="bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                Vendu
              </span>
            )}
          </div>

          {/* Favorite Button */}
          {onFavorite && (
            <button
              onClick={(e) => {
                e.preventDefault();
                onFavorite(listing.id);
              }}
              className={cn(
                'absolute top-3 right-3 p-2 rounded-full bg-white/90 backdrop-blur-sm shadow-sm transition-all duration-200 hover:scale-110',
                isFavorite ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
              )}
            >
              <Heart className={cn('w-5 h-5', isFavorite && 'fill-current')} />
            </button>
          )}
        </div>
      </Link>

      {/* Content */}
      <div className="p-4">
        <Link href={`/annonces/${listing.slug || listing.id}`}>
          <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors line-clamp-2">
            {listing.title}
          </h3>
        </Link>

        {/* Price */}
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-xl font-bold text-primary-600">
            {formatPrice(listing.price)}
          </span>
          {listing.original_price && listing.original_price > listing.price && (
            <span className="text-sm text-gray-400 line-through">
              {formatPrice(listing.original_price)}
            </span>
          )}
        </div>

        {/* Meta */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span className="flex items-center">
            <MapPin className="w-4 h-4 mr-1" />
            {listing.location}
          </span>
          <span className="flex items-center">
            <Clock className="w-4 h-4 mr-1" />
            {formatRelativeTime(listing.created_at)}
          </span>
        </div>

        {/* Stats */}
        {variant === 'default' && (
          <div className="flex items-center gap-4 mt-3 pt-3 border-t text-xs text-gray-400">
            <span className="flex items-center">
              <Eye className="w-3 h-3 mr-1" />
              {listing.views_count} vues
            </span>
            <span className="flex items-center">
              <Heart className="w-3 h-3 mr-1" />
              {listing.favorites_count} favoris
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// Skeleton pour le loading
export function ListingCardSkeleton() {
  return (
    <div className="card">
      <div className="aspect-[4/3] bg-gray-200 animate-pulse" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-gray-200 rounded animate-pulse" />
        <div className="h-6 w-24 bg-gray-200 rounded animate-pulse" />
        <div className="flex justify-between">
          <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
    </div>
  );
}

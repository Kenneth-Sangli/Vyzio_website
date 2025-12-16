"""
Service de gestion des assets (images/médias) avec Cloudinary.
Phase 5 - Stockage d'assets & CDN

Fonctionnalités:
- Upload d'images vers Cloudinary
- Génération de transformations (thumbnails, optimisations)
- URLs avec cache-control
- Nettoyage des images orphelines
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import Optional, Dict, List, Tuple
import logging
import hashlib
from io import BytesIO
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


# Transformations prédéfinies pour les images
IMAGE_TRANSFORMATIONS = {
    'thumbnail': {
        'width': 150,
        'height': 150,
        'crop': 'fill',
        'gravity': 'auto',
        'quality': 'auto:low',
        'fetch_format': 'auto',
    },
    'card': {
        'width': 400,
        'height': 300,
        'crop': 'fill',
        'gravity': 'auto',
        'quality': 'auto:good',
        'fetch_format': 'auto',
    },
    'detail': {
        'width': 800,
        'height': 600,
        'crop': 'limit',
        'quality': 'auto:best',
        'fetch_format': 'auto',
    },
    'full': {
        'width': 1200,
        'crop': 'limit',
        'quality': 'auto:best',
        'fetch_format': 'auto',
    },
    'avatar': {
        'width': 200,
        'height': 200,
        'crop': 'fill',
        'gravity': 'face',
        'quality': 'auto:good',
        'fetch_format': 'auto',
        'radius': 'max',
    },
    'avatar_small': {
        'width': 50,
        'height': 50,
        'crop': 'fill',
        'gravity': 'face',
        'quality': 'auto:low',
        'fetch_format': 'auto',
        'radius': 'max',
    },
}


def is_cloudinary_configured() -> bool:
    """Vérifie si Cloudinary est correctement configuré."""
    storage = getattr(settings, 'CLOUDINARY_STORAGE', {})
    return bool(
        storage.get('CLOUD_NAME') and 
        storage.get('API_KEY') and 
        storage.get('API_SECRET')
    )


def configure_cloudinary():
    """Configure Cloudinary avec les paramètres de settings."""
    if not is_cloudinary_configured():
        logger.warning("Cloudinary n'est pas configuré. Les uploads utiliseront le stockage local.")
        return False
    
    storage = settings.CLOUDINARY_STORAGE
    cloudinary.config(
        cloud_name=storage['CLOUD_NAME'],
        api_key=storage['API_KEY'],
        api_secret=storage['API_SECRET'],
        secure=True,
    )
    return True


def upload_image(
    file,
    folder: str = 'listings',
    public_id: Optional[str] = None,
    transformation: Optional[Dict] = None,
    tags: Optional[List[str]] = None,
    overwrite: bool = False,
) -> Dict:
    """
    Upload une image vers Cloudinary.
    
    Args:
        file: Fichier image (InMemoryUploadedFile ou chemin)
        folder: Dossier de destination sur Cloudinary
        public_id: ID public personnalisé (optionnel)
        transformation: Transformation à appliquer à l'upload
        tags: Tags pour organiser les images
        overwrite: Écraser si existe déjà
        
    Returns:
        Dict avec les informations de l'image uploadée
    """
    if not configure_cloudinary():
        # Fallback: retourner un mock pour le dev local
        return {
            'public_id': public_id or 'local_image',
            'secure_url': '/media/placeholder.jpg',
            'url': '/media/placeholder.jpg',
            'width': 800,
            'height': 600,
            'format': 'jpg',
            'bytes': 0,
            'is_local': True,
        }
    
    upload_options = {
        'folder': folder,
        'overwrite': overwrite,
        'resource_type': 'image',
        'unique_filename': True,
        'use_filename': True,
        'invalidate': True,  # Invalider le cache CDN
    }
    
    if public_id:
        upload_options['public_id'] = public_id
    
    if transformation:
        upload_options['transformation'] = transformation
    
    if tags:
        upload_options['tags'] = tags
    
    # Optimisation automatique
    upload_options['eager'] = [
        IMAGE_TRANSFORMATIONS['thumbnail'],
        IMAGE_TRANSFORMATIONS['card'],
    ]
    upload_options['eager_async'] = True  # Génération async des transformations
    
    try:
        result = cloudinary.uploader.upload(file, **upload_options)
        logger.info(f"Image uploadée: {result.get('public_id')}")
        return result
    except Exception as e:
        logger.error(f"Erreur upload Cloudinary: {e}")
        raise


def delete_image(public_id: str) -> bool:
    """
    Supprime une image de Cloudinary.
    
    Args:
        public_id: ID public de l'image
        
    Returns:
        True si suppression réussie
    """
    if not configure_cloudinary():
        return True
    
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        return result.get('result') == 'ok'
    except Exception as e:
        logger.error(f"Erreur suppression Cloudinary: {e}")
        return False


def get_image_url(
    public_id: str,
    transformation: str = 'full',
    custom_transformation: Optional[Dict] = None,
) -> str:
    """
    Génère une URL d'image avec transformation.
    
    Args:
        public_id: ID public de l'image
        transformation: Nom de la transformation prédéfinie
        custom_transformation: Transformation personnalisée
        
    Returns:
        URL de l'image transformée
    """
    if not is_cloudinary_configured():
        return f'/media/{public_id}'
    
    transform = custom_transformation or IMAGE_TRANSFORMATIONS.get(transformation, {})
    
    return cloudinary.CloudinaryImage(public_id).build_url(**transform)


def get_image_urls(public_id: str) -> Dict[str, str]:
    """
    Génère toutes les URLs de variantes pour une image.
    
    Args:
        public_id: ID public de l'image
        
    Returns:
        Dict avec toutes les variantes d'URL
    """
    if not is_cloudinary_configured():
        base_url = f'/media/{public_id}'
        return {name: base_url for name in IMAGE_TRANSFORMATIONS.keys()}
    
    urls = {}
    for name, transform in IMAGE_TRANSFORMATIONS.items():
        urls[name] = cloudinary.CloudinaryImage(public_id).build_url(**transform)
    
    return urls


def get_responsive_image_srcset(
    public_id: str,
    widths: List[int] = [320, 640, 960, 1280, 1920],
) -> str:
    """
    Génère un srcset responsive pour une image.
    
    Args:
        public_id: ID public de l'image
        widths: Largeurs pour le srcset
        
    Returns:
        String srcset pour l'attribut HTML
    """
    if not is_cloudinary_configured():
        return f'/media/{public_id}'
    
    srcset_parts = []
    for width in widths:
        url = cloudinary.CloudinaryImage(public_id).build_url(
            width=width,
            crop='limit',
            quality='auto',
            fetch_format='auto',
        )
        srcset_parts.append(f'{url} {width}w')
    
    return ', '.join(srcset_parts)


def validate_image(file) -> Tuple[bool, Optional[str]]:
    """
    Valide un fichier image.
    
    Args:
        file: Fichier à valider
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Taille max: 10MB
    max_size = 10 * 1024 * 1024
    
    # Types autorisés
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    
    # Extensions autorisées
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Vérifier le type MIME
    content_type = getattr(file, 'content_type', None)
    if content_type and content_type not in allowed_types:
        return False, f"Type de fichier non autorisé: {content_type}"
    
    # Vérifier l'extension
    filename = getattr(file, 'name', '')
    if filename:
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{ext}' not in allowed_extensions:
            return False, f"Extension non autorisée: {ext}"
    
    # Vérifier la taille
    size = getattr(file, 'size', 0)
    if size > max_size:
        return False, f"Fichier trop volumineux ({size // 1024 // 1024}MB > 10MB)"
    
    # Vérifier que c'est une vraie image avec PIL
    try:
        if hasattr(file, 'read'):
            file.seek(0)
            img = PILImage.open(file)
            img.verify()
            file.seek(0)
    except Exception as e:
        return False, f"Fichier image invalide: {str(e)}"
    
    return True, None


def optimize_image_before_upload(
    file,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 85,
) -> BytesIO:
    """
    Optimise une image avant upload (réduction taille, compression).
    
    Args:
        file: Fichier image
        max_width: Largeur maximale
        max_height: Hauteur maximale
        quality: Qualité JPEG (1-100)
        
    Returns:
        BytesIO avec l'image optimisée
    """
    if hasattr(file, 'read'):
        file.seek(0)
    
    img = PILImage.open(file)
    
    # Convertir en RGB si nécessaire (pour JPEG)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Redimensionner si trop grand
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
    
    # Sauvegarder en JPEG optimisé
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return output


def get_image_hash(file) -> str:
    """
    Calcule un hash MD5 d'une image pour déduplication.
    
    Args:
        file: Fichier image
        
    Returns:
        Hash MD5 de l'image
    """
    if hasattr(file, 'read'):
        file.seek(0)
        content = file.read()
        file.seek(0)
    else:
        content = file
    
    return hashlib.sha256(content).hexdigest()


# ==================== Nettoyage des images orphelines ====================

def find_orphaned_images(folder: str = 'listings') -> List[Dict]:
    """
    Trouve les images orphelines sur Cloudinary.
    Compare les images Cloudinary avec la base de données.
    
    Args:
        folder: Dossier à scanner
        
    Returns:
        Liste des images orphelines
    """
    if not configure_cloudinary():
        return []
    
    from apps.listings.models import ListingImage
    
    orphaned = []
    
    try:
        # Récupérer toutes les images du dossier Cloudinary
        result = cloudinary.api.resources(
            type='upload',
            prefix=folder,
            max_results=500,
        )
        
        cloudinary_images = {r['public_id'] for r in result.get('resources', [])}
        
        # Récupérer les public_ids en base
        # Note: Il faut extraire le public_id de l'URL stockée
        db_images = set()
        for img in ListingImage.objects.all():
            if img.image and hasattr(img.image, 'public_id'):
                db_images.add(img.image.public_id)
        
        # Trouver les orphelines
        orphan_ids = cloudinary_images - db_images
        
        for public_id in orphan_ids:
            orphaned.append({
                'public_id': public_id,
                'url': cloudinary.CloudinaryImage(public_id).build_url(),
            })
        
        logger.info(f"Trouvé {len(orphaned)} images orphelines dans {folder}")
        
    except Exception as e:
        logger.error(f"Erreur scan images orphelines: {e}")
    
    return orphaned


def cleanup_orphaned_images(
    folder: str = 'listings',
    dry_run: bool = True,
    max_delete: int = 100,
) -> Dict:
    """
    Supprime les images orphelines.
    
    Args:
        folder: Dossier à nettoyer
        dry_run: Si True, simule seulement (ne supprime pas)
        max_delete: Nombre max d'images à supprimer
        
    Returns:
        Rapport de nettoyage
    """
    orphaned = find_orphaned_images(folder)
    
    report = {
        'scanned_folder': folder,
        'orphaned_found': len(orphaned),
        'deleted': 0,
        'errors': 0,
        'dry_run': dry_run,
        'details': [],
    }
    
    for i, img in enumerate(orphaned[:max_delete]):
        if dry_run:
            report['details'].append({
                'public_id': img['public_id'],
                'action': 'would_delete',
            })
        else:
            success = delete_image(img['public_id'])
            if success:
                report['deleted'] += 1
                report['details'].append({
                    'public_id': img['public_id'],
                    'action': 'deleted',
                })
            else:
                report['errors'] += 1
                report['details'].append({
                    'public_id': img['public_id'],
                    'action': 'error',
                })
    
    return report


# ==================== Gestion du cache CDN ====================

def invalidate_cdn_cache(public_ids: List[str]) -> bool:
    """
    Invalide le cache CDN pour les images spécifiées.
    
    Args:
        public_ids: Liste des public_ids à invalider
        
    Returns:
        True si réussi
    """
    if not configure_cloudinary():
        return True
    
    try:
        for public_id in public_ids:
            cloudinary.uploader.explicit(
                public_id,
                type='upload',
                invalidate=True,
            )
        return True
    except Exception as e:
        logger.error(f"Erreur invalidation cache: {e}")
        return False


def get_cloudinary_usage() -> Dict:
    """
    Récupère les statistiques d'utilisation Cloudinary.
    
    Returns:
        Dict avec storage, bandwidth, transformations utilisés
    """
    if not configure_cloudinary():
        return {'error': 'Cloudinary non configuré'}
    
    try:
        usage = cloudinary.api.usage()
        return {
            'storage': {
                'used_bytes': usage.get('storage', {}).get('usage', 0),
                'limit_bytes': usage.get('storage', {}).get('limit', 0),
                'used_percent': usage.get('storage', {}).get('used_percent', 0),
            },
            'bandwidth': {
                'used_bytes': usage.get('bandwidth', {}).get('usage', 0),
                'limit_bytes': usage.get('bandwidth', {}).get('limit', 0),
                'used_percent': usage.get('bandwidth', {}).get('used_percent', 0),
            },
            'transformations': {
                'used': usage.get('transformations', {}).get('usage', 0),
                'limit': usage.get('transformations', {}).get('limit', 0),
                'used_percent': usage.get('transformations', {}).get('used_percent', 0),
            },
            'plan': usage.get('plan', 'unknown'),
        }
    except Exception as e:
        logger.error(f"Erreur récupération usage Cloudinary: {e}")
        return {'error': str(e)}

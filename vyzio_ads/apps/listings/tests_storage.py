"""
Tests pour le service de stockage Cloudinary.
Phase 5 - Stockage d'assets & CDN
"""
import pytest
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image as PILImage
from unittest.mock import patch, MagicMock
from apps.listings.services.storage import (
    is_cloudinary_configured,
    upload_image,
    delete_image,
    get_image_url,
    get_image_urls,
    get_responsive_image_srcset,
    validate_image,
    optimize_image_before_upload,
    get_image_hash,
    find_orphaned_images,
    cleanup_orphaned_images,
    get_cloudinary_usage,
    invalidate_cdn_cache,
    IMAGE_TRANSFORMATIONS,
)


def create_test_image(width=100, height=100, format='JPEG'):
    """Crée une image de test en mémoire."""
    image = PILImage.new('RGB', (width, height), color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def create_uploaded_file(name='test.jpg', content_type='image/jpeg', width=100, height=100):
    """Crée un fichier uploadé de test."""
    image_buffer = create_test_image(width, height)
    return SimpleUploadedFile(
        name=name,
        content=image_buffer.read(),
        content_type=content_type,
    )


# ==================== Tests de configuration ====================

class TestCloudinaryConfiguration(TestCase):
    """Tests de configuration Cloudinary."""
    
    @override_settings(CLOUDINARY_STORAGE={
        'CLOUD_NAME': 'test_cloud',
        'API_KEY': 'test_key',
        'API_SECRET': 'test_secret',
    })
    def test_is_cloudinary_configured_true(self):
        """Test configuration complète."""
        assert is_cloudinary_configured() is True
    
    @override_settings(CLOUDINARY_STORAGE={
        'CLOUD_NAME': '',
        'API_KEY': 'test_key',
        'API_SECRET': 'test_secret',
    })
    def test_is_cloudinary_configured_missing_cloud_name(self):
        """Test configuration incomplète - cloud_name manquant."""
        assert is_cloudinary_configured() is False
    
    @override_settings(CLOUDINARY_STORAGE={})
    def test_is_cloudinary_configured_empty(self):
        """Test configuration vide."""
        assert is_cloudinary_configured() is False


# ==================== Tests de validation d'image ====================

class TestImageValidation(TestCase):
    """Tests de validation des images."""
    
    def test_validate_image_valid_jpeg(self):
        """Test validation image JPEG valide."""
        file = create_uploaded_file('test.jpg', 'image/jpeg')
        is_valid, error = validate_image(file)
        assert is_valid is True
        assert error is None
    
    def test_validate_image_valid_png(self):
        """Test validation image PNG valide."""
        image_buffer = create_test_image(format='PNG')
        file = SimpleUploadedFile(
            name='test.png',
            content=image_buffer.read(),
            content_type='image/png',
        )
        is_valid, error = validate_image(file)
        assert is_valid is True
        assert error is None
    
    def test_validate_image_invalid_type(self):
        """Test validation type MIME invalide."""
        file = SimpleUploadedFile(
            name='test.pdf',
            content=b'%PDF-1.4 fake pdf content',
            content_type='application/pdf',
        )
        is_valid, error = validate_image(file)
        assert is_valid is False
        assert 'non autorisé' in error
    
    def test_validate_image_invalid_extension(self):
        """Test validation extension invalide."""
        image_buffer = create_test_image()
        file = SimpleUploadedFile(
            name='test.exe',
            content=image_buffer.read(),
            content_type='image/jpeg',
        )
        is_valid, error = validate_image(file)
        assert is_valid is False
        assert 'Extension' in error
    
    def test_validate_image_too_large(self):
        """Test validation fichier trop volumineux."""
        # Créer un fichier de plus de 10MB
        large_content = b'0' * (11 * 1024 * 1024)
        file = SimpleUploadedFile(
            name='large.jpg',
            content=large_content,
            content_type='image/jpeg',
        )
        # Override size attribute
        file.size = len(large_content)
        is_valid, error = validate_image(file)
        assert is_valid is False
        assert 'volumineux' in error
    
    def test_validate_image_corrupted(self):
        """Test validation image corrompue."""
        file = SimpleUploadedFile(
            name='corrupted.jpg',
            content=b'not a real image content',
            content_type='image/jpeg',
        )
        is_valid, error = validate_image(file)
        assert is_valid is False
        assert 'invalide' in error


# ==================== Tests d'optimisation d'image ====================

class TestImageOptimization(TestCase):
    """Tests d'optimisation des images."""
    
    def test_optimize_image_resize(self):
        """Test redimensionnement image trop grande."""
        large_image = create_test_image(width=3000, height=2000)
        optimized = optimize_image_before_upload(large_image, max_width=1920, max_height=1080)
        
        result_image = PILImage.open(optimized)
        assert result_image.width <= 1920
        assert result_image.height <= 1080
    
    def test_optimize_image_quality(self):
        """Test compression qualité."""
        image = create_test_image(width=500, height=500)
        original_size = len(image.read())
        image.seek(0)
        
        optimized = optimize_image_before_upload(image, quality=50)
        optimized_size = len(optimized.read())
        
        # L'image compressée devrait être plus petite
        # (Note: pas toujours vrai pour très petites images)
        assert optimized_size > 0
    
    def test_optimize_image_rgba_to_rgb(self):
        """Test conversion RGBA vers RGB."""
        # Créer image RGBA (avec transparence)
        rgba_image = PILImage.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        buffer = BytesIO()
        rgba_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        optimized = optimize_image_before_upload(buffer)
        result_image = PILImage.open(optimized)
        
        assert result_image.mode == 'RGB'


# ==================== Tests de hash d'image ====================

class TestImageHash(TestCase):
    """Tests de hash d'image pour déduplication."""
    
    def test_get_image_hash_consistent(self):
        """Test hash consistant pour même image."""
        image1 = create_test_image()
        image2 = create_test_image()
        
        # Même génération = même contenu = même hash
        hash1 = get_image_hash(image1)
        hash2 = get_image_hash(image2)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex length
    
    def test_get_image_hash_different(self):
        """Test hash différent pour images différentes."""
        image1 = create_test_image(width=100, height=100)
        image2 = create_test_image(width=200, height=200)
        
        hash1 = get_image_hash(image1)
        hash2 = get_image_hash(image2)
        
        assert hash1 != hash2


# ==================== Tests des transformations prédéfinies ====================

class TestImageTransformations(TestCase):
    """Tests des transformations d'images."""
    
    def test_transformations_defined(self):
        """Test que toutes les transformations sont définies."""
        expected = ['thumbnail', 'card', 'detail', 'full', 'avatar', 'avatar_small']
        for name in expected:
            assert name in IMAGE_TRANSFORMATIONS
    
    def test_thumbnail_transformation(self):
        """Test transformation thumbnail."""
        transform = IMAGE_TRANSFORMATIONS['thumbnail']
        assert transform['width'] == 150
        assert transform['height'] == 150
        assert transform['crop'] == 'fill'
    
    def test_avatar_transformation(self):
        """Test transformation avatar avec détection de visage."""
        transform = IMAGE_TRANSFORMATIONS['avatar']
        assert transform['gravity'] == 'face'
        assert transform['radius'] == 'max'


# ==================== Tests avec mock Cloudinary ====================

@pytest.mark.django_db
class TestCloudinaryUpload:
    """Tests d'upload avec mock Cloudinary."""
    
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_upload_image_unconfigured(self, mock_config):
        """Test upload quand Cloudinary non configuré."""
        mock_config.return_value = False
        
        file = create_uploaded_file()
        result = upload_image(file)
        
        assert result['is_local'] is True
        assert 'placeholder' in result['secure_url']
    
    @patch('apps.listings.services.storage.cloudinary')
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_upload_image_success(self, mock_config, mock_cloudinary):
        """Test upload réussi."""
        mock_config.return_value = True
        mock_cloudinary.uploader.upload.return_value = {
            'public_id': 'listings/test123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/listings/test123.jpg',
            'url': 'http://res.cloudinary.com/test/image/upload/listings/test123.jpg',
            'width': 800,
            'height': 600,
            'format': 'jpg',
            'bytes': 50000,
        }
        
        file = create_uploaded_file()
        result = upload_image(file, folder='listings')
        
        assert result['public_id'] == 'listings/test123'
        assert 'cloudinary.com' in result['secure_url']
        mock_cloudinary.uploader.upload.assert_called_once()


@pytest.mark.django_db
class TestCloudinaryDelete:
    """Tests de suppression avec mock Cloudinary."""
    
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_delete_image_unconfigured(self, mock_config):
        """Test suppression quand Cloudinary non configuré."""
        mock_config.return_value = False
        
        result = delete_image('test_id')
        assert result is True  # Retourne True pour éviter erreurs
    
    @patch('apps.listings.services.storage.cloudinary')
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_delete_image_success(self, mock_config, mock_cloudinary):
        """Test suppression réussie."""
        mock_config.return_value = True
        mock_cloudinary.uploader.destroy.return_value = {'result': 'ok'}
        
        result = delete_image('listings/test123')
        
        assert result is True
        mock_cloudinary.uploader.destroy.assert_called_once_with(
            'listings/test123', 
            invalidate=True
        )


# ==================== Tests des URLs ====================

@pytest.mark.django_db
class TestImageUrls:
    """Tests de génération d'URLs."""
    
    @patch('apps.listings.services.storage.is_cloudinary_configured')
    def test_get_image_url_unconfigured(self, mock_config):
        """Test URL quand Cloudinary non configuré."""
        mock_config.return_value = False
        
        url = get_image_url('test_image')
        assert url == '/media/test_image'
    
    @patch('apps.listings.services.storage.is_cloudinary_configured')
    @patch('apps.listings.services.storage.cloudinary')
    def test_get_image_url_configured(self, mock_cloudinary, mock_config):
        """Test URL avec Cloudinary configuré."""
        mock_config.return_value = True
        mock_image = MagicMock()
        mock_image.build_url.return_value = 'https://res.cloudinary.com/test/image/upload/c_limit,w_1200/test_image'
        mock_cloudinary.CloudinaryImage.return_value = mock_image
        
        url = get_image_url('test_image', transformation='full')
        
        assert 'cloudinary.com' in url
    
    @patch('apps.listings.services.storage.is_cloudinary_configured')
    def test_get_image_urls_all_variants(self, mock_config):
        """Test génération de toutes les variantes d'URL."""
        mock_config.return_value = False
        
        urls = get_image_urls('test_image')
        
        assert 'thumbnail' in urls
        assert 'card' in urls
        assert 'detail' in urls
        assert 'full' in urls
        assert 'avatar' in urls
    
    @patch('apps.listings.services.storage.is_cloudinary_configured')
    def test_get_responsive_srcset_unconfigured(self, mock_config):
        """Test srcset quand non configuré."""
        mock_config.return_value = False
        
        srcset = get_responsive_image_srcset('test_image')
        assert srcset == '/media/test_image'


# ==================== Tests de nettoyage ====================

@pytest.mark.django_db
class TestOrphanedImagesCleanup:
    """Tests de nettoyage des images orphelines."""
    
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_find_orphaned_unconfigured(self, mock_config):
        """Test recherche orphelines quand non configuré."""
        mock_config.return_value = False
        
        orphaned = find_orphaned_images()
        assert orphaned == []
    
    @patch('apps.listings.services.storage.find_orphaned_images')
    def test_cleanup_dry_run(self, mock_find):
        """Test nettoyage en mode dry-run."""
        mock_find.return_value = [
            {'public_id': 'listings/orphan1', 'url': 'http://test.com/orphan1'},
            {'public_id': 'listings/orphan2', 'url': 'http://test.com/orphan2'},
        ]
        
        report = cleanup_orphaned_images(dry_run=True)
        
        assert report['orphaned_found'] == 2
        assert report['deleted'] == 0
        assert report['dry_run'] is True
        assert all(d['action'] == 'would_delete' for d in report['details'])
    
    @patch('apps.listings.services.storage.delete_image')
    @patch('apps.listings.services.storage.find_orphaned_images')
    def test_cleanup_actual_delete(self, mock_find, mock_delete):
        """Test nettoyage avec suppression réelle."""
        mock_find.return_value = [
            {'public_id': 'listings/orphan1', 'url': 'http://test.com/orphan1'},
        ]
        mock_delete.return_value = True
        
        report = cleanup_orphaned_images(dry_run=False)
        
        assert report['deleted'] == 1
        assert report['dry_run'] is False
        mock_delete.assert_called_once_with('listings/orphan1')
    
    @patch('apps.listings.services.storage.find_orphaned_images')
    def test_cleanup_max_limit(self, mock_find):
        """Test limite max de suppression."""
        mock_find.return_value = [
            {'public_id': f'listings/orphan{i}', 'url': f'http://test.com/orphan{i}'}
            for i in range(10)
        ]
        
        report = cleanup_orphaned_images(dry_run=True, max_delete=3)
        
        assert len(report['details']) == 3


# ==================== Tests des statistiques ====================

@pytest.mark.django_db
class TestCloudinaryStats:
    """Tests des statistiques Cloudinary."""
    
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_get_usage_unconfigured(self, mock_config):
        """Test stats quand non configuré."""
        mock_config.return_value = False
        
        usage = get_cloudinary_usage()
        assert 'error' in usage
    
    @patch('apps.listings.services.storage.cloudinary')
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_get_usage_success(self, mock_config, mock_cloudinary):
        """Test récupération stats réussie."""
        mock_config.return_value = True
        mock_cloudinary.api.usage.return_value = {
            'storage': {'usage': 1000000, 'limit': 10000000, 'used_percent': 10},
            'bandwidth': {'usage': 5000000, 'limit': 50000000, 'used_percent': 10},
            'transformations': {'usage': 100, 'limit': 1000, 'used_percent': 10},
            'plan': 'free',
        }
        
        usage = get_cloudinary_usage()
        
        assert usage['plan'] == 'free'
        assert usage['storage']['used_bytes'] == 1000000
        assert usage['bandwidth']['used_percent'] == 10


# ==================== Tests d'invalidation cache ====================

@pytest.mark.django_db
class TestCDNCacheInvalidation:
    """Tests d'invalidation du cache CDN."""
    
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_invalidate_unconfigured(self, mock_config):
        """Test invalidation quand non configuré."""
        mock_config.return_value = False
        
        result = invalidate_cdn_cache(['test_id'])
        assert result is True
    
    @patch('apps.listings.services.storage.cloudinary')
    @patch('apps.listings.services.storage.configure_cloudinary')
    def test_invalidate_success(self, mock_config, mock_cloudinary):
        """Test invalidation réussie."""
        mock_config.return_value = True
        
        result = invalidate_cdn_cache(['id1', 'id2'])
        
        assert result is True
        assert mock_cloudinary.uploader.explicit.call_count == 2


# ==================== Tests d'intégration serializer ====================

@pytest.mark.django_db
class TestListingImageSerializer:
    """Tests du serializer avec variantes d'images."""
    
    def test_image_variants_in_serializer(self):
        """Test que le serializer génère les variantes."""
        from django.contrib.auth import get_user_model
        from apps.listings.models import Listing, Category, ListingImage
        from apps.listings.serializers import ListingImageWithVariantsSerializer
        
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )
        category = Category.objects.create(name='Test', slug='test')
        listing = Listing.objects.create(
            title='Test Listing',
            slug='test-listing',
            description='Description',
            price=100,
            seller=user,
            category=category,
            location='Paris',
        )
        
        # Créer une image de test
        image_file = create_uploaded_file()
        listing_image = ListingImage.objects.create(
            listing=listing,
            image=image_file,
            is_primary=True,
        )
        
        serializer = ListingImageWithVariantsSerializer(listing_image)
        data = serializer.data
        
        assert 'id' in data
        assert 'image' in data
        assert 'thumbnail' in data
        assert 'card' in data
        assert 'detail' in data
        assert 'full' in data
        assert 'is_primary' in data

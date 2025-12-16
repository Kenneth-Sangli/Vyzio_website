"""
Commande de management pour nettoyer les images orphelines.

Usage:
    python manage.py cleanup_images --dry-run  # Simuler
    python manage.py cleanup_images            # Supprimer réellement
    python manage.py cleanup_images --folder=avatars --max=50
"""
from django.core.management.base import BaseCommand
from apps.listings.services.storage import (
    cleanup_orphaned_images,
    find_orphaned_images,
    get_cloudinary_usage,
    is_cloudinary_configured,
)


class Command(BaseCommand):
    help = 'Nettoie les images orphelines de Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler le nettoyage sans supprimer',
        )
        parser.add_argument(
            '--folder',
            type=str,
            default='listings',
            help='Dossier Cloudinary à scanner (défaut: listings)',
        )
        parser.add_argument(
            '--max',
            type=int,
            default=100,
            help='Nombre maximum d\'images à supprimer (défaut: 100)',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Afficher les statistiques d\'utilisation Cloudinary',
        )

    def handle(self, *args, **options):
        # Vérifier la configuration Cloudinary
        if not is_cloudinary_configured():
            self.stdout.write(
                self.style.WARNING('⚠️  Cloudinary n\'est pas configuré. Opération annulée.')
            )
            return

        # Afficher les stats si demandé
        if options['stats']:
            self._display_stats()
            return

        folder = options['folder']
        dry_run = options['dry_run']
        max_delete = options['max']

        self.stdout.write(f'\n📁 Scan du dossier: {folder}')
        self.stdout.write(f'🔍 Mode: {"Simulation (dry-run)" if dry_run else "Suppression réelle"}')
        self.stdout.write(f'🔢 Maximum: {max_delete} images\n')

        # Trouver les images orphelines
        self.stdout.write('Recherche des images orphelines...')
        orphaned = find_orphaned_images(folder)
        
        if not orphaned:
            self.stdout.write(self.style.SUCCESS('✅ Aucune image orpheline trouvée !'))
            return

        self.stdout.write(f'Trouvé {len(orphaned)} images orphelines\n')

        # Exécuter le nettoyage
        report = cleanup_orphaned_images(
            folder=folder,
            dry_run=dry_run,
            max_delete=max_delete,
        )

        # Afficher le rapport
        self._display_report(report)

    def _display_report(self, report):
        """Affiche le rapport de nettoyage."""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 RAPPORT DE NETTOYAGE')
        self.stdout.write('=' * 50)
        
        self.stdout.write(f'Dossier scanné: {report["scanned_folder"]}')
        self.stdout.write(f'Images orphelines trouvées: {report["orphaned_found"]}')
        
        if report['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'⚠️  Mode simulation - {report["orphaned_found"]} images auraient été supprimées'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Images supprimées: {report["deleted"]}'))
            if report['errors'] > 0:
                self.stdout.write(self.style.ERROR(f'❌ Erreurs: {report["errors"]}'))

        # Détails
        if report['details'] and len(report['details']) <= 20:
            self.stdout.write('\nDétails:')
            for item in report['details']:
                action = item['action']
                if action == 'deleted':
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {item["public_id"]}'))
                elif action == 'would_delete':
                    self.stdout.write(f'  ○ {item["public_id"]} (serait supprimé)')
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ {item["public_id"]} (erreur)'))

    def _display_stats(self):
        """Affiche les statistiques Cloudinary."""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 STATISTIQUES CLOUDINARY')
        self.stdout.write('=' * 50)

        usage = get_cloudinary_usage()
        
        if 'error' in usage:
            self.stdout.write(self.style.ERROR(f'Erreur: {usage["error"]}'))
            return

        self.stdout.write(f'\n📦 Plan: {usage["plan"]}')
        
        # Storage
        storage = usage['storage']
        storage_mb = storage['used_bytes'] / (1024 * 1024)
        self.stdout.write(f'\n💾 Stockage: {storage_mb:.2f} MB ({storage["used_percent"]:.1f}%)')
        
        # Bandwidth
        bandwidth = usage['bandwidth']
        bandwidth_mb = bandwidth['used_bytes'] / (1024 * 1024)
        self.stdout.write(f'📡 Bande passante: {bandwidth_mb:.2f} MB ({bandwidth["used_percent"]:.1f}%)')
        
        # Transformations
        transforms = usage['transformations']
        self.stdout.write(f'🔄 Transformations: {transforms["used"]} ({transforms["used_percent"]:.1f}%)')

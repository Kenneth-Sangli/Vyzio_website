"""
Command to setup initial data for production:
- Subscription Plans
- Categories
- Credit Packs
"""
from django.core.management.base import BaseCommand
from apps.payments.models import SubscriptionPlan, PostCreditPack
from apps.listings.models import Category


class Command(BaseCommand):
    help = 'Setup initial data for production (plans, categories, credit packs)'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        self.create_subscription_plans()
        self.create_categories()
        self.create_credit_packs()
        
        self.stdout.write(self.style.SUCCESS('✅ Initial data setup complete!'))

    def create_subscription_plans(self):
        """Create subscription plans"""
        self.stdout.write('Creating subscription plans...')
        
        plans = [
            {
                'name': 'Basic Mensuel',
                'slug': 'basic-monthly',
                'plan_type': 'basic',
                'billing_cycle': 'monthly',
                'price': 9.99,
                'max_listings': 10,
                'max_images_per_listing': 5,
                'can_boost': False,
                'boost_count_per_month': 0,
                'featured_badge': False,
                'priority_support': False,
                'analytics_access': False,
                'description': 'Idéal pour commencer à vendre',
                'features_list': [
                    '10 annonces actives',
                    '5 photos par annonce',
                    'Messagerie illimitée',
                    'Support standard'
                ],
                'is_active': True,
                'is_popular': False,
                'sort_order': 1,
            },
            {
                'name': 'Basic Annuel',
                'slug': 'basic-yearly',
                'plan_type': 'basic',
                'billing_cycle': 'yearly',
                'price': 99.99,
                'max_listings': 10,
                'max_images_per_listing': 5,
                'can_boost': False,
                'boost_count_per_month': 0,
                'featured_badge': False,
                'priority_support': False,
                'analytics_access': False,
                'description': 'Idéal pour commencer à vendre - 2 mois offerts',
                'features_list': [
                    '10 annonces actives',
                    '5 photos par annonce',
                    'Messagerie illimitée',
                    'Support standard',
                    '2 mois offerts'
                ],
                'is_active': True,
                'is_popular': False,
                'sort_order': 2,
            },
            {
                'name': 'Pro Mensuel',
                'slug': 'pro-monthly',
                'plan_type': 'pro',
                'billing_cycle': 'monthly',
                'price': 24.99,
                'max_listings': 50,
                'max_images_per_listing': 10,
                'can_boost': True,
                'boost_count_per_month': 5,
                'featured_badge': True,
                'priority_support': True,
                'analytics_access': True,
                'description': 'Pour les vendeurs réguliers',
                'features_list': [
                    '50 annonces actives',
                    '10 photos par annonce',
                    '5 boosts par mois',
                    'Badge vendeur Pro',
                    'Support prioritaire',
                    'Statistiques avancées'
                ],
                'is_active': True,
                'is_popular': True,
                'sort_order': 3,
            },
            {
                'name': 'Pro Annuel',
                'slug': 'pro-yearly',
                'plan_type': 'pro',
                'billing_cycle': 'yearly',
                'price': 249.99,
                'max_listings': 50,
                'max_images_per_listing': 10,
                'can_boost': True,
                'boost_count_per_month': 5,
                'featured_badge': True,
                'priority_support': True,
                'analytics_access': True,
                'description': 'Pour les vendeurs réguliers - 2 mois offerts',
                'features_list': [
                    '50 annonces actives',
                    '10 photos par annonce',
                    '5 boosts par mois',
                    'Badge vendeur Pro',
                    'Support prioritaire',
                    'Statistiques avancées',
                    '2 mois offerts'
                ],
                'is_active': True,
                'is_popular': False,
                'sort_order': 4,
            },
            {
                'name': 'Business Mensuel',
                'slug': 'business-monthly',
                'plan_type': 'business',
                'billing_cycle': 'monthly',
                'price': 49.99,
                'max_listings': -1,  # Illimité
                'max_images_per_listing': 20,
                'can_boost': True,
                'boost_count_per_month': 20,
                'featured_badge': True,
                'priority_support': True,
                'analytics_access': True,
                'description': 'Pour les professionnels',
                'features_list': [
                    'Annonces illimitées',
                    '20 photos par annonce',
                    '20 boosts par mois',
                    'Badge vendeur Business',
                    'Support VIP 24/7',
                    'Statistiques complètes',
                    'API Access'
                ],
                'is_active': True,
                'is_popular': False,
                'sort_order': 5,
            },
            {
                'name': 'Business Annuel',
                'slug': 'business-yearly',
                'plan_type': 'business',
                'billing_cycle': 'yearly',
                'price': 499.99,
                'max_listings': -1,  # Illimité
                'max_images_per_listing': 20,
                'can_boost': True,
                'boost_count_per_month': 20,
                'featured_badge': True,
                'priority_support': True,
                'analytics_access': True,
                'description': 'Pour les professionnels - 2 mois offerts',
                'features_list': [
                    'Annonces illimitées',
                    '20 photos par annonce',
                    '20 boosts par mois',
                    'Badge vendeur Business',
                    'Support VIP 24/7',
                    'Statistiques complètes',
                    'API Access',
                    '2 mois offerts'
                ],
                'is_active': True,
                'is_popular': False,
                'sort_order': 6,
            },
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  - {plan.name}: {status}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ {len(plans)} plans configured'))

    def create_categories(self):
        """Create listing categories"""
        self.stdout.write('Creating categories...')
        
        categories = [
            {'name': 'Électronique', 'slug': 'electronique', 'description': 'Smartphones, tablettes, accessoires...'},
            {'name': 'Informatique', 'slug': 'informatique', 'description': 'Ordinateurs, composants, périphériques...'},
            {'name': 'Véhicules', 'slug': 'vehicules', 'description': 'Voitures, motos, vélos...'},
            {'name': 'Immobilier', 'slug': 'immobilier', 'description': 'Ventes, locations, colocations...'},
            {'name': 'Mode', 'slug': 'mode', 'description': 'Vêtements, chaussures, accessoires...'},
            {'name': 'Maison & Jardin', 'slug': 'maison-jardin', 'description': 'Meubles, décoration, bricolage...'},
            {'name': 'Jeux & Loisirs', 'slug': 'jeux-loisirs', 'description': 'Jeux vidéo, consoles, sports...'},
            {'name': 'Photo & Vidéo', 'slug': 'photo-video', 'description': 'Appareils photo, caméras, drones...'},
            {'name': 'Services', 'slug': 'services', 'description': 'Cours, réparations, prestations...'},
            {'name': 'Emploi', 'slug': 'emploi', 'description': 'Offres d\'emploi, missions freelance...'},
            {'name': 'Autres', 'slug': 'autres', 'description': 'Tout le reste...'},
        ]
        
        for cat_data in categories:
            cat, created = Category.objects.update_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  - {cat.name}: {status}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ {len(categories)} categories configured'))

    def create_credit_packs(self):
        """Create credit packs for pay-per-post"""
        self.stdout.write('Creating credit packs...')
        
        packs = [
            {
                'name': 'Test - 1 Crédit',
                'slug': 'test-1-credit',
                'credits': 1,
                'price': 0.50,
                'description': '🧪 Pack de test à 0.50€',
                'is_active': True,
                'sort_order': 0,
            },
            {
                'name': '1 Crédit',
                'slug': '1-credit',
                'credits': 1,
                'price': 2.99,
                'description': 'Publiez 1 annonce',
                'is_active': True,
                'sort_order': 1,
            },
            {
                'name': '5 Crédits',
                'slug': '5-credits',
                'credits': 5,
                'price': 12.99,
                'bonus_credits': 0,
                'description': 'Publiez 5 annonces - Économisez 15%',
                'is_active': True,
                'is_popular': True,
                'sort_order': 2,
            },
            {
                'name': '10 Crédits',
                'slug': '10-credits',
                'credits': 10,
                'price': 24.99,
                'bonus_credits': 1,
                'description': 'Publiez 11 annonces - 1 offert!',
                'is_active': True,
                'sort_order': 3,
            },
            {
                'name': '25 Crédits',
                'slug': '25-credits',
                'credits': 25,
                'price': 54.99,
                'bonus_credits': 5,
                'description': 'Publiez 30 annonces - 5 offerts!',
                'is_active': True,
                'sort_order': 4,
            },
        ]
        
        for pack_data in packs:
            pack, created = PostCreditPack.objects.update_or_create(
                slug=pack_data['slug'],
                defaults=pack_data
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  - {pack.name}: {status}')
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ {len(packs)} credit packs configured'))

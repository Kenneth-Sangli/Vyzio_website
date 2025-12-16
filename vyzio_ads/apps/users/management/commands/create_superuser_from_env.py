"""
Custom management command to create a superuser from environment variables.
This is useful for platforms like Render free tier where shell access is not available.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config


class Command(BaseCommand):
    help = 'Create a superuser from environment variables if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get credentials from environment variables
        email = config('DJANGO_SUPERUSER_EMAIL', default='')
        password = config('DJANGO_SUPERUSER_PASSWORD', default='')
        username = config('DJANGO_SUPERUSER_USERNAME', default='')
        
        if not email or not password:
            self.stdout.write(
                self.style.WARNING('DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD must be set')
            )
            return
        
        # Use email as username if not provided
        if not username:
            username = email.split('@')[0]
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.SUCCESS(f'Superuser with email {email} already exists')
            )
            return
        
        # Create superuser
        try:
            user = User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser {email} created successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )

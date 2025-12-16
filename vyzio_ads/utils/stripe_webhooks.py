# Configuration Stripe Webhooks
# Webhook Handler pour Stripe

import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Webhook pour gérer les événements Stripe
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_payment_success(session)
    
    # Handle invoice.paid
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        handle_invoice_paid(invoice)
    
    # Handle invoice.payment_failed
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    # Handle customer.subscription.deleted
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)
    
    return JsonResponse({'status': 'success'})


def handle_payment_success(session):
    """Traiter un paiement réussi"""
    from apps.payments.models import Payment, Subscription
    from apps.users.models import CustomUser
    from django.utils import timezone
    from datetime import timedelta
    
    # Récupérer le payment
    try:
        payment = Payment.objects.get(stripe_payment_id=session.id)
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.save()
        
        # Créer/Mettre à jour l'abonnement
        if payment.subscription:
            if payment.subscription.billing_cycle == 'monthly':
                end_date = timezone.now() + timedelta(days=30)
            else:
                end_date = timezone.now() + timedelta(days=365)
            
            Subscription.objects.update_or_create(
                user=payment.user,
                defaults={
                    'plan': payment.subscription,
                    'status': 'active',
                    'ends_at': end_date,
                    'stripe_subscription_id': session.subscription,
                }
            )
        
        # Envoyer email de confirmation
        send_payment_confirmation_email(payment.user)
    
    except Payment.DoesNotExist:
        pass


def handle_invoice_paid(invoice):
    """Traiter une facture payée"""
    from apps.payments.models import Invoice
    from django.utils import timezone
    
    try:
        invoice_obj = Invoice.objects.get(stripe_id=invoice.id)
        invoice_obj.paid_at = timezone.now()
        invoice_obj.save()
    except Invoice.DoesNotExist:
        pass


def handle_payment_failed(invoice):
    """Traiter un paiement échoué"""
    pass  # Implémenter la logique


def handle_subscription_cancelled(subscription):
    """Traiter une annulation d'abonnement"""
    from apps.payments.models import Subscription
    from django.utils import timezone
    
    try:
        sub = Subscription.objects.get(stripe_subscription_id=subscription.id)
        sub.status = 'cancelled'
        sub.cancelled_at = timezone.now()
        sub.save()
    except Subscription.DoesNotExist:
        pass


def send_payment_confirmation_email(user):
    """Envoyer email de confirmation"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    subject = "Paiement confirmé - Vyzio Ads"
    html_message = render_to_string('emails/payment_confirmation.html', {'user': user})
    
    send_mail(
        subject,
        'Payment confirmation',
        'noreply@vyzio.com',
        [user.email],
        html_message=html_message,
        fail_silently=True,
    )

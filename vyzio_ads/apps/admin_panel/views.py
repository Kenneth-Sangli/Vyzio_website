from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum
from apps.listings.models import Listing
from apps.messaging.models import Report
from apps.payments.models import Payment
from .models import AdminAuditLog

User = get_user_model()

class AdminDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        return Response({
            'total_users': User.objects.count(),
            'sellers_count': User.objects.filter(role__in=['seller', 'professional']).count(),
            'total_listings': Listing.objects.count(),
            'published_listings': Listing.objects.filter(status='published').count(),
            'pending_listings': Listing.objects.filter(status='pending').count(),
            'total_transactions': Payment.objects.filter(status='completed').count(),
            'total_revenue': Payment.objects.filter(status='completed').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'reported_items': Report.objects.filter(is_resolved=False).count(),
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
            'active_users': User.objects.filter(last_login__gte=timezone.now() - timedelta(days=7)).count(),
        })
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """List all users with filters"""
        role = request.query_params.get('role')
        is_banned = request.query_params.get('is_banned')
        
        queryset = User.objects.all()
        
        if role:
            queryset = queryset.filter(role=role)
        if is_banned:
            queryset = queryset.filter(is_banned=is_banned.lower() == 'true')
        
        return Response({
            'count': queryset.count(),
            'users': [{
                'id': str(u.id),
                'email': u.email,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role,
                'is_banned': u.is_banned,
                'is_verified': getattr(u, 'is_verified', True),
                'created_at': u.date_joined,
            } for u in queryset]
        })
    
    @action(detail=False, methods=['post'])
    def ban_user(self, request):
        """Ban a user"""
        user_id = request.data.get('user_id')
        reason = request.data.get('reason', '')
        
        try:
            user = User.objects.get(id=user_id)
            user.is_banned = True
            user.save()
            
            # Log audit
            AdminAuditLog.objects.create(
                admin=request.user,
                action='ban_user',
                target_user=user,
                details=f'Reason: {reason}'
            )
            
            return Response({'status': 'User banned'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def unban_user(self, request):
        """Unban a user"""
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            user.is_banned = False
            user.save()
            
            # Log audit
            AdminAuditLog.objects.create(
                admin=request.user,
                action='unban_user',
                target_user=user,
                details='User unbanned'
            )
            
            return Response({'status': 'User unbanned'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def pending_listings(self, request):
        """Get pending listings for moderation"""
        listings = Listing.objects.filter(status='pending').select_related('seller', 'category').prefetch_related('images')
        
        return Response({
            'count': listings.count(),
            'listings': [{
                'id': str(l.id),
                'title': l.title,
                'price': float(l.price),
                'seller': {
                    'id': str(l.seller.id),
                    'email': l.seller.email,
                    'username': l.seller.username,
                },
                'category': l.category.name if l.category else None,
                'location': l.location,
                'created_at': l.created_at,
                'images': [{'image': img.image.url if img.image else None} for img in l.images.all()[:3]]
            } for l in listings]
        })
    
    @action(detail=False, methods=['post'])
    def approve_listing(self, request):
        """Approve a listing"""
        listing_id = request.data.get('listing_id')
        
        try:
            listing = Listing.objects.get(id=listing_id)
            listing.is_approved = True
            listing.status = 'published'
            listing.save()
            
            # Log audit
            AdminAuditLog.objects.create(
                admin=request.user,
                action='approve_listing',
                target_listing_id=str(listing.id),
                details=f'Approved listing: {listing.title}'
            )
            
            return Response({'status': 'Listing approved'})
        except Listing.DoesNotExist:
            return Response({'error': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def reject_listing(self, request):
        """Reject a listing"""
        listing_id = request.data.get('listing_id')
        reason = request.data.get('reason', '')
        
        try:
            listing = Listing.objects.get(id=listing_id)
            listing.is_approved = False
            listing.is_flagged = True
            listing.flag_reason = reason
            listing.save()
            
            # Log audit
            AdminAuditLog.objects.create(
                admin=request.user,
                action='reject_listing',
                target_listing_id=str(listing.id),
                details=f'Rejected listing: {listing.title}. Reason: {reason}'
            )
            
            return Response({'status': 'Listing rejected'})
        except Listing.DoesNotExist:
            return Response({'error': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Get user reports"""
        status_filter = request.query_params.get('status')
        
        queryset = Report.objects.all().select_related('reporter', 'reported_user')
        
        if status_filter == 'pending':
            queryset = queryset.filter(is_resolved=False)
        elif status_filter == 'resolved':
            queryset = queryset.filter(is_resolved=True)
        
        return Response({
            'count': queryset.count(),
            'reports': [{
                'id': str(r.id),
                'reporter': {
                    'id': str(r.reporter.id) if r.reporter else None,
                    'email': r.reporter.email if r.reporter else None,
                },
                'reported_user': {
                    'id': str(r.reported_user.id) if r.reported_user else None,
                    'email': r.reported_user.email if r.reported_user else None,
                },
                'reason': r.reason,
                'description': getattr(r, 'description', ''),
                'status': 'resolved' if r.is_resolved else 'pending',
                'created_at': r.created_at,
            } for r in queryset]
        })
    
    @action(detail=False, methods=['post'])
    def resolve_report(self, request):
        """Resolve a report"""
        report_id = request.data.get('report_id')
        action_taken = request.data.get('action', '')  # ban_user, delete_content, dismissed, resolved
        
        try:
            report = Report.objects.get(id=report_id)
            report.is_resolved = True
            report.save()
            
            # If action is to ban user
            if action_taken == 'ban_user' and report.reported_user:
                report.reported_user.is_banned = True
                report.reported_user.save()
                
                # Log ban audit
                AdminAuditLog.objects.create(
                    admin=request.user,
                    action='ban_user',
                    target_user=report.reported_user,
                    details=f'Banned from report resolution. Report reason: {report.reason}'
                )
            
            # Log report resolution audit
            AdminAuditLog.objects.create(
                admin=request.user,
                action='resolve_report',
                target_user=report.reported_user,
                details=f'Resolved report #{report.id}. Action: {action_taken}'
            )
            
            return Response({'status': 'Report resolved'})
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def audit_logs(self, request):
        """Get audit logs"""
        logs = AdminAuditLog.objects.all().select_related('admin', 'target_user').order_by('-created_at')[:100]
        
        return Response({
            'count': logs.count(),
            'logs': [{
                'id': log.id,
                'admin': log.admin.email if log.admin else None,
                'action': log.action,
                'target_user': log.target_user.email if log.target_user else None,
                'target_listing_id': log.target_listing_id,
                'details': log.details,
                'created_at': log.created_at,
            } for log in logs]
        })

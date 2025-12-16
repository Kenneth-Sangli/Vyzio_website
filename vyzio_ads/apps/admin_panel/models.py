
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminAuditLog(models.Model):
	"""Log d'audit pour toutes les actions admin/modération"""
	ACTION_CHOICES = [
		('suspend_user', 'Suspendre utilisateur'),
		('reactivate_user', 'Réactiver utilisateur'),
		('ban_user', 'Bannir utilisateur'),
		('unban_user', 'Débannir utilisateur'),
		('retire_listing', 'Retirer annonce'),
		('publish_listing', 'Remettre en ligne annonce'),
		('resolve_report', 'Résoudre signalement'),
		('other', 'Autre'),
	]
	id = models.UUIDField(primary_key=True, editable=False, auto_created=True)
	admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_actions')
	action = models.CharField(max_length=32, choices=ACTION_CHOICES)
	target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_targets')
	target_listing_id = models.CharField(max_length=64, blank=True)
	target_review_id = models.CharField(max_length=64, blank=True)
	details = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'admin_audit_log'
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.created_at} - {self.admin} - {self.action}"

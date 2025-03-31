from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Role choices
ROLE_CHOICES = (
    ('ADMIN', 'Administrator'),
    ('FACULTY', 'Faculty'),
)

class UserProfile(models.Model):
    """Extension of the User model to add role information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FACULTY')
    
    # Additional fields can be added here as needed
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

# Create a UserProfile automatically when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for a User if one doesn't exist"""
    UserProfile.objects.get_or_create(user=instance)

# Audit log for admin actions
class AdminActionLog(models.Model):
    """Log of administrative actions"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_actions')
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
    
    class Meta:
        verbose_name = "Admin Action Log"
        verbose_name_plural = "Admin Action Logs"
        ordering = ['-timestamp']

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when CustomUser is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when CustomUser is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=CustomUser)
def assign_user_group(sender, instance, created, **kwargs):
    """Assign user to appropriate group based on role"""
    update_fields = kwargs.get('update_fields') or []

    # Skip if not created and 'role' wasn't updated
    if not created and 'role' not in update_fields:
        return

    # Remove user from all role-based groups
    role_groups = Group.objects.filter(
        name__in=['ADMIN', 'PROPERTY_MANAGER', 'LANDLORD', 'TENANT']
    )
    instance.groups.remove(*role_groups)

    # Add user to appropriate group
    try:
        group = Group.objects.get(name=instance.role)
        instance.groups.add(group)
    except Group.DoesNotExist:
        # Group doesn't exist yet - will be created by management command
        pass

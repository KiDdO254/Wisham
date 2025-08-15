from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    """User role choices for the rental management system"""
    ADMIN = 'ADMIN', _('Administrator')
    PROPERTY_MANAGER = 'PROPERTY_MANAGER', _('Property Manager')
    LANDLORD = 'LANDLORD', _('Landlord')
    TENANT = 'TENANT', _('Tenant')


class CustomUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    
    # Phone number validator for Kenyan format
    phone_regex = RegexValidator(
        regex=r'^\+254[17]\d{8}$|^07\d{8}$|^01\d{8}$',
        message="Phone number must be in format: '+254712345678' or '0712345678'"
    )
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TENANT,
        help_text="User role in the system"
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        help_text="Phone number in Kenyan format"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_customuser'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def has_property_access(self, property_id):
        """Check if user can access specific property"""
        if self.role == Role.ADMIN:
            return True
        elif self.role == Role.PROPERTY_MANAGER:
            # Property managers can access properties they manage
            from properties.models import Property
            return Property.objects.filter(
                id=property_id,
                manager=self
            ).exists()
        elif self.role == Role.LANDLORD:
            # Landlords can access properties they own
            from properties.models import Property
            return Property.objects.filter(
                id=property_id,
                owner=self
            ).exists()
        elif self.role == Role.TENANT:
            # Tenants can access properties where they have rental units
            from properties.models import RentalUnit
            return RentalUnit.objects.filter(
                property_id=property_id,
                current_tenant=self
            ).exists()
        return False
    
    def get_accessible_properties(self):
        """Return queryset of properties user can access"""
        from properties.models import Property
        
        if self.role == Role.ADMIN:
            return Property.objects.all()
        elif self.role == Role.PROPERTY_MANAGER:
            return Property.objects.filter(manager=self)
        elif self.role == Role.LANDLORD:
            return Property.objects.filter(owner=self)
        elif self.role == Role.TENANT:
            # Get properties where user has rental units
            from properties.models import RentalUnit
            property_ids = RentalUnit.objects.filter(
                current_tenant=self
            ).values_list('property_id', flat=True)
            return Property.objects.filter(id__in=property_ids)
        return Property.objects.none()
    
    def save(self, *args, **kwargs):
        """Override save to assign user to appropriate group based on role"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new or 'role' in kwargs.get('update_fields', []):
            self.assign_role_permissions()
    
    def assign_role_permissions(self):
        """Assign user to appropriate group based on role"""
        # Remove user from all role-based groups
        role_groups = Group.objects.filter(
            name__in=[role.value for role in Role]
        )
        self.groups.remove(*role_groups)
        
        # Add user to appropriate group
        try:
            group = Group.objects.get(name=self.role)
            self.groups.add(group)
        except Group.DoesNotExist:
            # Group will be created by management command
            pass


class UserProfile(models.Model):
    """Additional user information and preferences"""
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(
        max_length=20,
        blank=True,
        help_text="Kenyan National ID number"
    )
    
    # Address Information
    county = models.CharField(max_length=50, blank=True)
    town = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[CustomUser.phone_regex]
    )
    
    # Preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('sw', 'Swahili'),
        ],
        default='en'
    )
    
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications"
    )
    
    sms_notifications = models.BooleanField(
        default=True,
        help_text="Receive SMS notifications"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_userprofile'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

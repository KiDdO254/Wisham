from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import os


class Amenity(models.Model):
    """Model representing property amenities"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class or emoji")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Property(models.Model):
    """Model representing a property with Kenya-specific fields"""
    
    # Kenya counties
    COUNTY_CHOICES = [
        ('nairobi', 'Nairobi'),
        ('mombasa', 'Mombasa'),
        ('kiambu', 'Kiambu'),
        ('nakuru', 'Nakuru'),
        ('machakos', 'Machakos'),
        ('kajiado', 'Kajiado'),
        ('kisumu', 'Kisumu'),
        ('uasin_gishu', 'Uasin Gishu'),
        ('meru', 'Meru'),
        ('nyeri', 'Nyeri'),
        ('murang\'a', 'Murang\'a'),
        ('kirinyaga', 'Kirinyaga'),
        ('embu', 'Embu'),
        ('kitui', 'Kitui'),
        ('makueni', 'Makueni'),
        ('other', 'Other'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('townhouse', 'Townhouse'),
        ('studio', 'Studio'),
        ('bedsitter', 'Bedsitter'),
        ('maisonette', 'Maisonette'),
        ('bungalow', 'Bungalow'),
        ('commercial', 'Commercial'),
        ('office', 'Office Space'),
    ]
    
    name = models.CharField(max_length=200)
    address = models.TextField()
    county = models.CharField(max_length=50, choices=COUNTY_CHOICES)
    town = models.CharField(max_length=100)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Commercial-specific fields
    number_of_floors = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Number of floors (required for commercial properties)"
    )
    units_per_floor = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Number of units per floor (required for commercial properties)"
    )
    
    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='owned_properties'
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_properties',
        help_text="Property manager (optional)"
    )
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='properties')
    
    # Contact information
    contact_phone = models.CharField(max_length=15, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['county', 'town']),
            models.Index(fields=['property_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Custom validation for commercial properties"""
        from django.core.exceptions import ValidationError
        
        if self.property_type == 'commercial':
            if not self.number_of_floors:
                raise ValidationError("Number of floors is required for commercial properties.")
            if not self.units_per_floor:
                raise ValidationError("Units per floor is required for commercial properties.")
            if self.number_of_floors and self.number_of_floors < 1:
                raise ValidationError("Number of floors must be at least 1.")
            if self.units_per_floor and self.units_per_floor < 1:
                raise ValidationError("Units per floor must be at least 1.")
    
    def get_total_units(self):
        """Calculate total units for commercial properties"""
        if self.property_type == 'commercial' and self.number_of_floors and self.units_per_floor:
            return self.number_of_floors * self.units_per_floor
        return None
    
    def is_commercial(self):
        """Check if property is commercial type"""
        return self.property_type == 'commercial'
    
    def get_available_units_count(self):
        """Return count of available rental units"""
        return self.units.filter(is_available=True).count()
    
    def get_total_units_count(self):
        """Return total count of rental units"""
        return self.units.count()


def property_image_upload_path(instance, filename):
    """Generate upload path for property images"""
    return f'properties/{instance.property.id}/images/{filename}'


class PropertyImage(models.Model):
    """Model for property photos with proper file handling"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=property_image_upload_path)
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary image for property listing")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['property', 'is_primary']),
            models.Index(fields=['property', 'order']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per property
        if self.is_primary:
            PropertyImage.objects.filter(
                property=self.property, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete the actual file when the model instance is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


class RentalUnit(models.Model):
    """Enhanced model representing a rental unit within a property"""
    UNIT_TYPES = [
        ('studio', 'Studio'),
        ('bedsitter', 'Bedsitter'),
        ('1br', '1 Bedroom'),
        ('2br', '2 Bedroom'),
        ('3br', '3 Bedroom'),
        ('4br', '4+ Bedroom'),
        ('maisonette', 'Maisonette'),
        ('penthouse', 'Penthouse'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('warehouse', 'Warehouse'),
        ('industrial', 'Industrial Space'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=50)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES)
    
    # Rental amounts in KES
    rent_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly rent in KES"
    )
    deposit_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Security deposit in KES"
    )
    
    # Unit details
    floor_area = models.PositiveIntegerField(null=True, blank=True, help_text="Floor area in square feet")
    floor_number = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Floor number (required for commercial properties)"
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    current_tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rented_units'
    )
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True)
    
    # Additional details
    description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['property', 'unit_number']
        ordering = ['property', 'floor_number', 'unit_number']
        indexes = [
            models.Index(fields=['property', 'is_available']),
            models.Index(fields=['unit_type']),
            models.Index(fields=['rent_amount']),
            models.Index(fields=['floor_number']),
        ]
    
    def __str__(self):
        if self.property.is_commercial() and self.floor_number:
            return f"{self.property.name} - Floor {self.floor_number}, Unit {self.unit_number}"
        return f"{self.property.name} - Unit {self.unit_number}"
    
    def get_rent_display(self):
        """Return formatted rent amount in KES"""
        return f"KES {self.rent_amount:,.2f}"
    
    def get_deposit_display(self):
        """Return formatted deposit amount in KES"""
        return f"KES {self.deposit_amount:,.2f}"
    
    def is_occupied(self):
        """Check if unit is currently occupied"""
        return not self.is_available and self.current_tenant is not None
    
    def clean(self):
        """Custom validation for commercial properties"""
        from django.core.exceptions import ValidationError
        
        if self.property.is_commercial():
            if not self.floor_number:
                raise ValidationError("Floor number is required for commercial properties.")
            if self.floor_number and self.property.number_of_floors:
                if self.floor_number > self.property.number_of_floors:
                    raise ValidationError(f"Floor number cannot exceed the total number of floors ({self.property.number_of_floors}).")
    
    def save(self, *args, **kwargs):
        """Override save to automatically update availability based on tenant status"""
        # Update availability based on whether there's a current tenant
        if self.current_tenant:
            self.is_available = False
        else:
            self.is_available = True
        
        super().save(*args, **kwargs)
    
    def get_floor_display(self):
        """Get formatted floor display"""
        if self.floor_number:
            if self.floor_number == 1:
                return "Ground Floor"
            elif self.floor_number == 2:
                return "1st Floor"
            elif self.floor_number == 3:
                return "2nd Floor"
            else:
                return f"{self.floor_number - 1}rd Floor"
        return "N/A"
    
    def get_commercial_unit_info(self):
        """Get commercial unit information"""
        if self.property.is_commercial():
            return {
                'floor': self.get_floor_display(),
                'floor_number': self.floor_number,
                'total_floors': self.property.number_of_floors,
                'units_per_floor': self.property.units_per_floor,
                'total_units': self.property.get_total_units()
            }
        return None

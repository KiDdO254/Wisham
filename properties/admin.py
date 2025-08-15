from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from .models import Property, RentalUnit, PropertyImage, Amenity


class PropertyImageInline(TabularInline):
    """Inline admin for property images"""
    model = PropertyImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'order']
    readonly_fields = ['created_at']


class RentalUnitInline(TabularInline):
    """Inline admin for rental units"""
    model = RentalUnit
    extra = 0
    fields = ['unit_number', 'unit_type', 'rent_amount', 'deposit_amount', 'is_available', 'current_tenant']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Amenity)
class AmenityAdmin(ModelAdmin):
    list_display = ['name', 'description', 'icon', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Amenity Information', {
            'fields': ('name', 'description', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Property)
class PropertyAdmin(ModelAdmin):
    list_display = [
        'name', 'property_type', 'county', 'town', 'owner', 
        'get_units_count', 'get_available_units', 'is_active', 'created_at'
    ]
    list_filter = [
        'property_type', 'county', 'is_active', 'created_at', 
        'owner', 'amenities'
    ]
    search_fields = ['name', 'address', 'town', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['amenities']
    inlines = [PropertyImageInline, RentalUnitInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'property_type')
        }),
        ('Commercial Details', {
            'fields': ('number_of_floors', 'units_per_floor'),
            'classes': ('collapse',),
            'description': 'Required for commercial properties only'
        }),
        ('Location (Kenya)', {
            'fields': ('address', 'county', 'town')
        }),
        ('Management', {
            'fields': ('owner', 'manager', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('contact_phone', 'contact_email')
        }),
        ('Amenities', {
            'fields': ('amenities',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_units_count(self, obj):
        """Display total units count"""
        return obj.get_total_units_count()
    get_units_count.short_description = 'Total Units'
    
    def get_available_units(self, obj):
        """Display available units count with color coding"""
        available = obj.get_available_units_count()
        total = obj.get_total_units_count()
        
        if total == 0:
            color = 'gray'
        elif available == 0:
            color = 'red'
        elif available < total / 2:
            color = 'orange'
        else:
            color = 'green'
            
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, available, total
        )
    get_available_units.short_description = 'Available/Total'


@admin.register(PropertyImage)
class PropertyImageAdmin(ModelAdmin):
    list_display = ['property', 'caption', 'is_primary', 'order', 'image_preview', 'created_at']
    list_filter = ['is_primary', 'created_at', 'property']
    search_fields = ['property__name', 'caption']
    readonly_fields = ['created_at', 'image_preview']
    list_editable = ['is_primary', 'order']
    
    fieldsets = (
        ('Image Information', {
            'fields': ('property', 'image', 'image_preview', 'caption')
        }),
        ('Display Settings', {
            'fields': ('is_primary', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(RentalUnit)
class RentalUnitAdmin(ModelAdmin):
    list_display = [
        'unit_number', 'property', 'unit_type', 'get_rent_display', 
        'get_deposit_display', 'is_available', 'current_tenant', 'floor_number'
    ]
    list_filter = [
        'property', 'unit_type', 'is_available', 'property__county', 
        'property__property_type', 'created_at'
    ]
    search_fields = [
        'unit_number', 'property__name', 'current_tenant__username', 
        'current_tenant__email', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_available']
    
    fieldsets = (
        ('Unit Information', {
            'fields': ('property', 'unit_number', 'unit_type', 'description')
        }),
        ('Physical Details', {
            'fields': ('floor_area', 'floor_number')
        }),
        ('Rental Details', {
            'fields': ('rent_amount', 'deposit_amount', 'is_available')
        }),
        ('Tenancy Information', {
            'fields': ('current_tenant', 'lease_start_date', 'lease_end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_rent_display(self, obj):
        """Display formatted rent amount"""
        return obj.get_rent_display()
    get_rent_display.short_description = 'Monthly Rent'
    
    def get_deposit_display(self, obj):
        """Display formatted deposit amount"""
        return obj.get_deposit_display()
    get_deposit_display.short_description = 'Security Deposit'

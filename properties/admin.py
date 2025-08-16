from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Property, RentalUnit, Amenity, PropertyImage, UnitReservation


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'order']


class RentalUnitInline(admin.TabularInline):
    model = RentalUnit
    extra = 1
    fields = ['unit_number', 'unit_type', 'rent_amount', 'deposit_amount', 'is_available']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'town', 'county', 'property_type', 'is_active', 'view_property_link']
    list_filter = ['property_type', 'county', 'town', 'is_active', 'created_at']
    search_fields = ['name', 'address', 'town', 'county']
    list_editable = ['is_active']
    inlines = [PropertyImageInline, RentalUnitInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'county', 'town', 'description')
        }),
        ('Property Details', {
            'fields': ('property_type', 'number_of_floors', 'units_per_floor')
        }),
        ('Contact Information', {
            'fields': ('contact_phone', 'contact_email')
        }),
        ('Ownership & Management', {
            'fields': ('owner', 'manager', 'amenities')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def view_property_link(self, obj):
        """Create a link to view the property on the frontend"""
        if obj.id:
            url = reverse('properties:property_detail', args=[obj.id])
            return format_html('<a href="{}" target="_blank">View Property</a>', url)
        return "N/A"
    view_property_link.short_description = "Frontend Link"


@admin.register(RentalUnit)
class RentalUnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'property', 'unit_type', 'rent_amount', 'deposit_amount', 'is_available', 'current_tenant']
    list_filter = ['unit_type', 'is_available', 'property__property_type', 'created_at']
    search_fields = ['unit_number', 'property__name', 'current_tenant__username']
    list_editable = ['is_available']
    
    fieldsets = (
        ('Unit Information', {
            'fields': ('property', 'unit_number', 'unit_type', 'description')
        }),
        ('Financial Details', {
            'fields': ('rent_amount', 'deposit_amount')
        }),
        ('Physical Details', {
            'fields': ('floor_number', 'floor_area')
        }),
        ('Tenancy', {
            'fields': ('is_available', 'current_tenant', 'lease_start_date', 'lease_end_date')
        }),
    )


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'icon']
    search_fields = ['name', 'description']
    list_editable = ['icon']


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['property', 'caption', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['property__name', 'caption']
    list_editable = ['is_primary', 'order']


@admin.register(UnitReservation)
class UnitReservationAdmin(admin.ModelAdmin):
    list_display = ['unit', 'tenant', 'status', 'reservation_date', 'intended_move_in_date', 'security_deposit_paid']
    list_filter = ['status', 'reservation_date', 'intended_move_in_date', 'security_deposit_paid']
    search_fields = ['unit__unit_number', 'tenant__username', 'tenant__email', 'unit__property__name']
    list_editable = ['status']
    
    fieldsets = (
        ('Reservation Details', {
            'fields': ('unit', 'tenant', 'status', 'reservation_date', 'intended_move_in_date')
        }),
        ('Payment Information', {
            'fields': ('security_deposit_paid', 'payment_reference', 'payment_date')
        }),
        ('Timing', {
            'fields': ('expires_at',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['reservation_date', 'expires_at']
    
    def get_queryset(self, request):
        """Optimize queries for related fields"""
        return super().get_queryset(request).select_related('unit', 'tenant', 'unit__property')

from django.contrib import admin
from .models import Payment, BankCardPayment, MPesaPayment, SecurityDeposit


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'tenant', 'rental_unit', 'property', 
        'payment_type', 'payment_method', 'amount', 'status', 'payment_date'
    ]
    list_filter = [
        'payment_type', 'payment_method', 'status', 'payment_date',
        'rental_unit__property__county'
    ]
    search_fields = [
        'reference_number', 'tenant__username', 'tenant__first_name', 
        'tenant__last_name', 'rental_unit__unit_number'
    ]
    readonly_fields = ['payment_id', 'reference_number', 'payment_date', 'processed_date']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'reference_number', 'tenant', 'rental_unit', 'property')
        }),
        ('Payment Details', {
            'fields': ('payment_type', 'payment_method', 'amount', 'status')
        }),
        ('Rent Payment Details', {
            'fields': ('months_paid_for', 'rent_period_start', 'rent_period_end'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('transaction_id', 'processed_date', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'tenant', 'rental_unit', 'property'
        )


@admin.register(BankCardPayment)
class BankCardPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment', 'card_type', 'card_number', 'cardholder_name', 
        'expiry_month', 'expiry_year', 'cvv_verified'
    ]
    list_filter = ['card_type', 'cvv_verified', 'expiry_year']
    search_fields = ['cardholder_name', 'billing_city', 'billing_state']
    readonly_fields = ['authorization_code']
    
    fieldsets = (
        ('Payment Reference', {
            'fields': ('payment',)
        }),
        ('Card Details', {
            'fields': ('card_type', 'card_number', 'expiry_month', 'expiry_year')
        }),
        ('Cardholder Information', {
            'fields': ('cardholder_name', 'billing_address', 'billing_city', 
                      'billing_state', 'billing_zip', 'billing_country')
        }),
        ('Processing', {
            'fields': ('authorization_code', 'cvv_verified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MPesaPayment)
class MPesaPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment', 'phone_number', 'transaction_type', 'mpesa_status',
        'initiated_at', 'completed_at'
    ]
    list_filter = ['transaction_type', 'mpesa_status', 'initiated_at']
    search_fields = ['phone_number', 'mpesa_receipt_number']
    readonly_fields = ['checkout_request_id', 'merchant_request_id']
    
    fieldsets = (
        ('Payment Reference', {
            'fields': ('payment',)
        }),
        ('MPesa Details', {
            'fields': ('phone_number', 'transaction_type', 'mpesa_status')
        }),
        ('Transaction IDs', {
            'fields': ('mpesa_receipt_number', 'checkout_request_id', 'merchant_request_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecurityDeposit)
class SecurityDepositAdmin(admin.ModelAdmin):
    list_display = [
        'tenant', 'rental_unit', 'amount', 'is_paid', 'is_refunded',
        'created_at', 'payment_date'
    ]
    list_filter = ['is_paid', 'is_refunded', 'created_at']
    search_fields = [
        'tenant__username', 'tenant__first_name', 'tenant__last_name',
        'rental_unit__unit_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Deposit Information', {
            'fields': ('tenant', 'rental_unit', 'amount')
        }),
        ('Payment Status', {
            'fields': ('is_paid', 'payment_date')
        }),
        ('Refund Status', {
            'fields': ('is_refunded', 'refund_date', 'refund_amount'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'tenant', 'rental_unit'
        )

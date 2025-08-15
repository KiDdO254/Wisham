from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class Payment(models.Model):
    """Model representing a payment made by a tenant"""
    
    PAYMENT_TYPES = [
        ('rent', 'Rent Payment'),
        ('security_deposit', 'Security Deposit'),
        ('other', 'Other Payment'),
    ]
    
    PAYMENT_METHODS = [
        ('mpesa', 'MPesa'),
        ('bank_card', 'Bank Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Payment identification
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference_number = models.CharField(max_length=50, unique=True, help_text="Payment reference number")
    
    # Payment details
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    rental_unit = models.ForeignKey('properties.RentalUnit', on_delete=models.CASCADE, related_name='payments')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='payments')
    
    # Payment information
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='rent')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Rent payment specific fields
    months_paid_for = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        null=True, 
        blank=True,
        help_text="Number of months this payment covers (1-6 months)"
    )
    rent_period_start = models.DateField(null=True, blank=True)
    rent_period_end = models.DateField(null=True, blank=True)
    
    # Payment status and processing
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="External transaction ID")
    
    # Timestamps
    payment_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['tenant', 'payment_date']),
            models.Index(fields=['rental_unit', 'payment_date']),
            models.Index(fields=['status', 'payment_date']),
            models.Index(fields=['payment_type', 'payment_date']),
        ]
    
    def __str__(self):
        return f"{self.tenant.username} - {self.payment_type} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_amount_display(self):
        """Return formatted amount in KES"""
        return f"KES {self.amount:,.2f}"
    
    def get_rent_period_display(self):
        """Return formatted rent period"""
        if self.rent_period_start and self.rent_period_end:
            return f"{self.rent_period_start.strftime('%b %Y')} - {self.rent_period_end.strftime('%b %Y')}"
        return "Not specified"


class BankCardPayment(models.Model):
    """Model for bank card payment details"""
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='bank_card_details')
    
    # Card details (encrypted in production)
    card_number = models.CharField(max_length=20, help_text="Last 4 digits of card")
    card_type = models.CharField(max_length=20, choices=[
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ])
    expiry_month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    expiry_year = models.PositiveIntegerField()
    
    # Billing information
    cardholder_name = models.CharField(max_length=100)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_zip = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100, default='Kenya')
    
    # Processing details
    authorization_code = models.CharField(max_length=100, blank=True)
    cvv_verified = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['card_type', 'expiry_year']),
        ]
    
    def __str__(self):
        return f"Card ending in {self.card_number} for {self.payment.tenant.username}"


class MPesaPayment(models.Model):
    """Model for MPesa payment details"""
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='mpesa_details')
    
    # MPesa specific fields
    phone_number = models.CharField(max_length=15, help_text="MPesa registered phone number")
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=[
        ('paybill', 'Pay Bill'),
        ('buygoods', 'Buy Goods'),
        ('sendmoney', 'Send Money'),
    ], default='paybill')
    
    # Status tracking
    mpesa_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ], default='pending')
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['phone_number', 'mpesa_status']),
            models.Index(fields=['mpesa_receipt_number']),
        ]
    
    def __str__(self):
        return f"MPesa {self.phone_number} - {self.payment.amount}"


class SecurityDeposit(models.Model):
    """Model for tracking security deposits"""
    
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='security_deposits')
    rental_unit = models.ForeignKey('properties.RentalUnit', on_delete=models.CASCADE, related_name='security_deposits')
    
    # Deposit details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Deposit status
    is_refunded = models.BooleanField(default=False)
    refund_date = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['tenant', 'rental_unit']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_paid']),
            models.Index(fields=['rental_unit', 'is_paid']),
        ]
    
    def __str__(self):
        return f"{self.tenant.username} - {self.rental_unit} - {self.amount}"
    
    def get_amount_display(self):
        """Return formatted amount in KES"""
        return f"KES {self.amount:,.2f}"
    
    def calculate_deposit_amount(self):
        """Calculate security deposit as 113% of monthly rent"""
        return self.rental_unit.rent_amount * Decimal('1.13')
    
    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.calculate_deposit_amount()
        super().save(*args, **kwargs)

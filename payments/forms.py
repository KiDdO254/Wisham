from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Payment, BankCardPayment, MPesaPayment, SecurityDeposit
from properties.models import RentalUnit


class PaymentForm(forms.ModelForm):
    """Form for creating payments"""
    
    class Meta:
        model = Payment
        fields = [
            'rental_unit', 'payment_type', 'payment_method', 'amount',
            'months_paid_for', 'rent_period_start', 'rent_period_end', 'notes'
        ]
        widgets = {
            'rental_unit': forms.Select(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'months_paid_for': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '6'}),
            'rent_period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rent_period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.role == 'TENANT':
            # Filter rental units to only show units rented by the current tenant
            self.fields['rental_unit'].queryset = RentalUnit.objects.filter(
                current_tenant=user,
                is_available=False
            )
        
        # Set initial values for rent period
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['rent_period_start'].initial = today
            self.fields['months_paid_for'].initial = 1
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        months_paid_for = cleaned_data.get('months_paid_for')
        rent_period_start = cleaned_data.get('rent_period_start')
        rent_period_end = cleaned_data.get('rent_period_end')
        amount = cleaned_data.get('amount')
        rental_unit = cleaned_data.get('rental_unit')
        
        if payment_type == 'rent':
            # Validate months paid for
            if not months_paid_for:
                raise forms.ValidationError("Number of months is required for rent payments.")
            
            if months_paid_for < 1 or months_paid_for > 6:
                raise forms.ValidationError("Rent payments can only cover 1-6 months.")
            
            # Calculate and validate rent period
            if rent_period_start:
                rent_period_end = rent_period_start + timedelta(days=30 * months_paid_for)
                cleaned_data['rent_period_end'] = rent_period_end
            
            # Validate amount matches the months
            if rental_unit and amount:
                expected_amount = rental_unit.rent_amount * months_paid_for
                if amount != expected_amount:
                    raise forms.ValidationError(
                        f"Amount should be KES {expected_amount:,.2f} for {months_paid_for} month(s) "
                        f"(KES {rental_unit.rent_amount:,.2f} per month)"
                    )
        
        return cleaned_data


class BankCardPaymentForm(forms.ModelForm):
    """Form for bank card payment details"""
    
    class Meta:
        model = BankCardPayment
        fields = [
            'card_number', 'card_type', 'expiry_month', 'expiry_year',
            'cardholder_name', 'billing_address', 'billing_city', 
            'billing_state', 'billing_zip', 'billing_country'
        ]
        widgets = {
            'card_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234 5678 9012 3456',
                'maxlength': '19'
            }),
            'card_type': forms.Select(attrs={'class': 'form-control'}),
            'expiry_month': forms.Select(
                choices=[(i, f"{i:02d}") for i in range(1, 13)],
                attrs={'class': 'form-control'}
            ),
            'expiry_year': forms.Select(
                choices=[(i, str(i)) for i in range(timezone.now().year, timezone.now().year + 11)],
                attrs={'class': 'form-control'}
            ),
            'cardholder_name': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'billing_city': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_state': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_zip': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']
        # Remove spaces and validate
        card_number = card_number.replace(' ', '')
        if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
            raise forms.ValidationError("Please enter a valid card number.")
        return card_number
    
    def clean_expiry_year(self):
        year = self.cleaned_data['expiry_year']
        month = self.cleaned_data.get('expiry_month')
        
        if month and year:
            expiry_date = datetime(year, month, 1)
            if expiry_date < timezone.now().replace(day=1):
                raise forms.ValidationError("Card has expired.")
        
        return year


class MPesaPaymentForm(forms.ModelForm):
    """Form for MPesa payment details"""
    
    class Meta:
        model = MPesaPayment
        fields = ['phone_number', 'transaction_type']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '254700000000',
                'pattern': '254[0-9]{9}'
            }),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        # Validate Kenyan phone number format
        if not phone_number.startswith('254') or len(phone_number) != 12:
            raise forms.ValidationError("Please enter a valid Kenyan phone number starting with 254.")
        return phone_number


class SecurityDepositForm(forms.ModelForm):
    """Form for security deposit payments"""
    
    class Meta:
        model = SecurityDeposit
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        rental_unit = kwargs.pop('rental_unit', None)
        super().__init__(*args, **kwargs)
        
        if rental_unit:
            # Calculate security deposit as 113% of monthly rent
            deposit_amount = rental_unit.rent_amount * Decimal('1.13')
            self.fields['amount'].initial = deposit_amount
            self.fields['amount'].help_text = f"Security deposit: 113% of monthly rent (KES {rental_unit.rent_amount:,.2f}) = KES {deposit_amount:,.2f}"


class PaymentMethodSelectionForm(forms.Form):
    """Form for selecting payment method"""
    
    PAYMENT_METHODS = [
        ('mpesa', 'MPesa'),
        ('bank_card', 'Bank Card'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Select Payment Method"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update({'class': 'form-check-input'})


class RentPaymentForm(forms.Form):
    """Form for rent payment details"""
    
    months_paid_for = forms.IntegerField(
        min_value=1,
        max_value=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '6'
        }),
        help_text="Select number of months to pay for (1-6 months)"
    )
    
    def __init__(self, *args, **kwargs):
        rental_unit = kwargs.pop('rental_unit', None)
        super().__init__(*args, **kwargs)
        
        if rental_unit:
            self.fields['months_paid_for'].help_text = (
                f"Monthly rent: KES {rental_unit.rent_amount:,.2f}. "
                "Select number of months to pay for (1-6 months)"
            )

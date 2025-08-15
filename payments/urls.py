from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Tenant payment URLs
    path('dashboard/', views.payment_dashboard, name='dashboard'),
    path('make-payment/', views.make_payment, name='make_payment'),
    path('mpesa-payment/', views.mpesa_payment, name='mpesa_payment'),
    path('bank-card-payment/', views.bank_card_payment, name='bank_card_payment'),
    
    # Security deposit payments
    path('security-deposit/mpesa/', views.security_deposit_mpesa, name='security_deposit_mpesa'),
    path('security-deposit/bank-card/', views.security_deposit_bank_card, name='security_deposit_bank_card'),
    
    # Rent payments
    path('rent-payment/mpesa/', views.rent_payment_mpesa, name='rent_payment_mpesa'),
    path('rent-payment/bank-card/', views.rent_payment_bank_card, name='rent_payment_bank_card'),
    
    # Payment success
    path('payment-success/<uuid:payment_id>/', views.payment_success, name='payment_success'),
    
    # Management URLs (for property managers, landlords, admin)
    path('view-payments/', views.view_payments, name='view_payments'),
    path('payment-details/<uuid:payment_id>/', views.payment_details, name='payment_details'),
    path('update-status/<uuid:payment_id>/', views.update_payment_status, name='update_payment_status'),
]

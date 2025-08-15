from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Payment, BankCardPayment, MPesaPayment, SecurityDeposit
from .forms import (
    PaymentForm, BankCardPaymentForm, MPesaPaymentForm, 
    SecurityDepositForm, PaymentMethodSelectionForm, RentPaymentForm
)
from properties.models import RentalUnit
from users.models import Role


@login_required
def payment_dashboard(request):
    """Payment dashboard for tenants"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can access the payment dashboard.")
    
    # Get tenant's rental units
    rental_units = RentalUnit.objects.filter(
        current_tenant=request.user,
        is_available=False
    )
    
    # Get security deposit status
    security_deposits = SecurityDeposit.objects.filter(tenant=request.user)
    
    # Get recent payments
    recent_payments = Payment.objects.filter(
        tenant=request.user
    ).order_by('-payment_date')[:5]
    
    # Calculate total paid and outstanding
    total_paid = Payment.objects.filter(
        tenant=request.user,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'rental_units': rental_units,
        'security_deposits': security_deposits,
        'recent_payments': recent_payments,
        'total_paid': total_paid,
    }
    
    return render(request, 'payments/tenant_dashboard.html', context)


@login_required
def make_payment(request):
    """Make a new payment"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    # Get tenant's rental units
    rental_units = RentalUnit.objects.filter(
        current_tenant=request.user,
        is_available=False
    )
    
    if not rental_units.exists():
        messages.error(request, "You don't have any rental units to make payments for.")
        return redirect('payments:dashboard')
    
    # Check if security deposit is paid
    security_deposit_paid = True
    for unit in rental_units:
        deposit, created = SecurityDeposit.objects.get_or_create(
            tenant=request.user,
            rental_unit=unit,
            defaults={'amount': unit.rent_amount * Decimal('1.13')}
        )
        if not deposit.is_paid:
            security_deposit_paid = False
            break
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'mpesa':
            return redirect('payments:mpesa_payment')
        elif payment_method == 'bank_card':
            return redirect('payments:bank_card_payment')
        else:
            messages.error(request, "Please select a valid payment method.")
    
    # Show payment method selection
    method_form = PaymentMethodSelectionForm()
    
    context = {
        'rental_units': rental_units,
        'security_deposit_paid': security_deposit_paid,
        'method_form': method_form,
    }
    
    return render(request, 'payments/make_payment.html', context)


@login_required
def mpesa_payment(request):
    """Process MPesa payment"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    rental_units = RentalUnit.objects.filter(
        current_tenant=request.user,
        is_available=False
    )
    
    if request.method == 'POST':
        # Handle payment type selection
        payment_type = request.POST.get('payment_type')
        
        if payment_type == 'security_deposit':
            return redirect('payments:security_deposit_mpesa')
        elif payment_type == 'rent':
            return redirect('payments:rent_payment_mpesa')
        else:
            messages.error(request, "Please select a valid payment type.")
    
    context = {
        'rental_units': rental_units,
    }
    
    return render(request, 'payments/mpesa_payment.html', context)


@login_required
def bank_card_payment(request):
    """Process bank card payment"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    rental_units = RentalUnit.objects.filter(
        current_tenant=request.user,
        is_available=False
    )
    
    if request.method == 'POST':
        # Handle payment type selection
        payment_type = request.POST.get('payment_type')
        
        if payment_type == 'security_deposit':
            return redirect('payments:security_deposit_bank_card')
        elif payment_type == 'rent':
            return redirect('payments:rent_payment_bank_card')
        else:
            messages.error(request, "Please select a valid payment type.")
    
    context = {
        'rental_units': rental_units,
    }
    
    return render(request, 'payments/bank_card_payment.html', context)


@login_required
def security_deposit_mpesa(request):
    """Pay security deposit via MPesa"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    rental_unit_id = request.GET.get('unit')
    rental_unit = get_object_or_404(RentalUnit, id=rental_unit_id, current_tenant=request.user)
    
    # Get or create security deposit record
    deposit, created = SecurityDeposit.objects.get_or_create(
        tenant=request.user,
        rental_unit=rental_unit,
        defaults={'amount': rental_unit.rent_amount * Decimal('1.13')}
    )
    
    if deposit.is_paid:
        messages.info(request, "Security deposit has already been paid for this unit.")
        return redirect('payments:dashboard')
    
    if request.method == 'POST':
        mpesa_form = MPesaPaymentForm(request.POST)
        if mpesa_form.is_valid():
            # Create payment record
            payment = Payment.objects.create(
                tenant=request.user,
                rental_unit=rental_unit,
                property=rental_unit.property,
                payment_type='security_deposit',
                payment_method='mpesa',
                amount=deposit.amount,
                status='pending'
            )
            
            # Create MPesa payment record
            mpesa_payment = mpesa_form.save(commit=False)
            mpesa_payment.payment = payment
            mpesa_payment.save()
            
            # Simulate MPesa processing (in production, integrate with actual MPesa API)
            messages.success(request, f"MPesa payment initiated for security deposit: {deposit.get_amount_display()}")
            return redirect('payments:payment_success', payment_id=payment.payment_id)
    
    mpesa_form = MPesaPaymentForm()
    
    context = {
        'rental_unit': rental_unit,
        'deposit': deposit,
        'mpesa_form': mpesa_form,
    }
    
    return render(request, 'payments/security_deposit_mpesa.html', context)


@login_required
def security_deposit_bank_card(request):
    """Pay security deposit via bank card"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    rental_unit_id = request.GET.get('unit')
    rental_unit = get_object_or_404(RentalUnit, id=rental_unit_id, current_tenant=request.user)
    
    # Get or create security deposit record
    deposit, created = SecurityDeposit.objects.get_or_create(
        tenant=request.user,
        rental_unit=rental_unit,
        defaults={'amount': rental_unit.rent_amount * Decimal('1.13')}
    )
    
    if deposit.is_paid:
        messages.info(request, "Security deposit has already been paid for this unit.")
        return redirect('payments:dashboard')
    
    if request.method == 'POST':
        card_form = BankCardPaymentForm(request.POST)
        if card_form.is_valid():
            # Create payment record
            payment = Payment.objects.create(
                tenant=request.user,
                rental_unit=rental_unit,
                property=rental_unit.property,
                payment_type='security_deposit',
                payment_method='bank_card',
                amount=deposit.amount,
                status='pending'
            )
            
            # Create bank card payment record
            card_payment = card_form.save(commit=False)
            card_payment.payment = payment
            card_payment.save()
            
            # Simulate card processing (in production, integrate with payment gateway)
            messages.success(request, f"Bank card payment processed for security deposit: {deposit.get_amount_display()}")
            return redirect('payments:payment_success', payment_id=payment.payment_id)
    
    card_form = BankCardPaymentForm()
    
    context = {
        'rental_unit': rental_unit,
        'deposit': deposit,
        'card_form': card_form,
    }
    
    return render(request, 'payments/security_deposit_bank_card.html', context)


@login_required
def rent_payment_mpesa(request):
    """Pay rent via MPesa"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    rental_unit_id = request.GET.get('unit')
    rental_unit = get_object_or_404(RentalUnit, id=rental_unit_id, current_tenant=request.user)
    
    # Check if security deposit is paid
    deposit, created = SecurityDeposit.objects.get_or_create(
        tenant=request.user,
        rental_unit=rental_unit,
        defaults={'amount': rental_unit.rent_amount * Decimal('1.13')}
    )
    
    if not deposit.is_paid:
        messages.error(request, "Security deposit must be paid before making rent payments.")
        return redirect('payments:make_payment')
    
    if request.method == 'POST':
        rent_form = RentPaymentForm(request.POST)
        mpesa_form = MPesaPaymentForm(request.POST)
        
        if rent_form.is_valid() and mpesa_form.is_valid():
            months = rent_form.cleaned_data['months_paid_for']
            amount = rental_unit.rent_amount * months
            
            # Create payment record
            payment = Payment.objects.create(
                tenant=request.user,
                rental_unit=rental_unit,
                property=rental_unit.property,
                payment_type='rent',
                payment_method='mpesa',
                amount=amount,
                months_paid_for=months,
                rent_period_start=timezone.now().date(),
                rent_period_end=timezone.now().date() + timedelta(days=30 * months),
                status='pending'
            )
            
            # Create MPesa payment record
            mpesa_payment = mpesa_form.save(commit=False)
            mpesa_payment.payment = payment
            mpesa_payment.save()
            
            messages.success(request, f"MPesa rent payment initiated: {payment.get_amount_display()} for {months} month(s)")
            return redirect('payments:payment_success', payment_id=payment.payment_id)
    
    rent_form = RentPaymentForm(rental_unit=rental_unit)
    mpesa_form = MPesaPaymentForm()
    
    context = {
        'rental_unit': rental_unit,
        'rent_form': rent_form,
        'mpesa_form': mpesa_form,
    }
    
    return render(request, 'payments/rent_payment_mpesa.html', context)


@login_required
def rent_payment_bank_card(request):
    """Pay rent via bank card"""
    if request.user.role != Role.TENANT:
        return HttpResponseForbidden("Only tenants can make payments.")
    
    rental_unit_id = request.GET.get('unit')
    rental_unit = get_object_or_404(RentalUnit, id=rental_unit_id, current_tenant=request.user)
    
    # Check if security deposit is paid
    deposit, created = SecurityDeposit.objects.get_or_create(
        tenant=request.user,
        rental_unit=rental_unit,
        defaults={'amount': rental_unit.rent_amount * Decimal('1.13')}
    )
    
    if not deposit.is_paid:
        messages.error(request, "Security deposit must be paid before making rent payments.")
        return redirect('payments:make_payment')
    
    if request.method == 'POST':
        rent_form = RentPaymentForm(request.POST)
        card_form = BankCardPaymentForm(request.POST)
        
        if rent_form.is_valid() and card_form.is_valid():
            months = rent_form.cleaned_data['months_paid_for']
            amount = rental_unit.rent_amount * months
            
            # Create payment record
            payment = Payment.objects.create(
                tenant=request.user,
                rental_unit=rental_unit,
                property=rental_unit.property,
                payment_type='rent',
                payment_method='bank_card',
                amount=amount,
                months_paid_for=months,
                rent_period_start=timezone.now().date(),
                rent_period_end=timezone.now().date() + timedelta(days=30 * months),
                status='pending'
            )
            
            # Create bank card payment record
            card_payment = card_form.save(commit=False)
            card_payment.payment = payment
            card_payment.save()
            
            messages.success(request, f"Bank card rent payment processed: {payment.get_amount_display()} for {months} month(s)")
            return redirect('payments:payment_success', payment_id=payment.payment_id)
    
    rent_form = RentPaymentForm(rental_unit=rental_unit)
    card_form = BankCardPaymentForm()
    
    context = {
        'rental_unit': rental_unit,
        'rent_form': rent_form,
        'card_form': card_form,
    }
    
    return render(request, 'payments/rent_payment_bank_card.html', context)


@login_required
def payment_success(request, payment_id):
    """Payment success page"""
    payment = get_object_or_404(Payment, payment_id=payment_id, tenant=request.user)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/payment_success.html', context)


@login_required
def view_payments(request):
    """View payments for property managers, landlords, and admin"""
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to view payments.")
    
    # Get payments based on user role
    if request.user.role == Role.ADMIN:
        payments = Payment.objects.all()
    elif request.user.role == Role.PROPERTY_MANAGER:
        payments = Payment.objects.filter(property__manager=request.user)
    elif request.user.role == Role.LANDLORD:
        payments = Payment.objects.filter(property__owner=request.user)
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Filter by payment type if provided
    payment_type_filter = request.GET.get('payment_type')
    if payment_type_filter:
        payments = payments.filter(payment_type=payment_type_filter)
    
    # Search by tenant name
    search_query = request.GET.get('search')
    if search_query:
        payments = payments.filter(
            Q(tenant__first_name__icontains=search_query) |
            Q(tenant__last_name__icontains=search_query) |
            Q(tenant__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_payments = payments.count()
    total_amount = payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    pending_payments = payments.filter(status='pending').count()
    
    context = {
        'page_obj': page_obj,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'pending_payments': pending_payments,
        'status_filter': status_filter,
        'payment_type_filter': payment_type_filter,
        'search_query': search_query,
    }
    
    return render(request, 'payments/view_payments.html', context)


@login_required
def payment_details(request, payment_id):
    """View detailed payment information"""
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to view payment details.")
    
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    # Check if user has permission to view this payment
    if request.user.role == Role.PROPERTY_MANAGER and payment.property.manager != request.user:
        return HttpResponseForbidden("You don't have permission to view this payment.")
    elif request.user.role == Role.LANDLORD and payment.property.owner != request.user:
        return HttpResponseForbidden("You don't have permission to view this payment.")
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/payment_details.html', context)


@login_required
def update_payment_status(request, payment_id):
    """Update payment status (admin/property manager only)"""
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER]:
        return HttpResponseForbidden("You don't have permission to update payment status.")
    
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Payment.PAYMENT_STATUS):
            payment.status = new_status
            if new_status == 'completed':
                payment.processed_date = timezone.now()
                
                # If this is a security deposit payment, mark it as paid
                if payment.payment_type == 'security_deposit':
                    deposit, created = SecurityDeposit.objects.get_or_create(
                        tenant=payment.tenant,
                        rental_unit=payment.rental_unit
                    )
                    deposit.is_paid = True
                    deposit.payment_date = timezone.now()
                    deposit.save()
            
            payment.save()
            messages.success(request, f"Payment status updated to {new_status}")
        else:
            messages.error(request, "Invalid payment status")
    
    return redirect('payments:payment_details', payment_id=payment_id)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import Property, RentalUnit, Amenity, PropertyImage, UnitReservation
from .forms import PropertyForm, PropertyImageForm, RentalUnitForm, AmenityForm, UnitReservationForm
from users.models import CustomUser
from django.urls import reverse


def property_list(request):
    """Display list of all properties"""
    from .models import Property
    # Get properties with their images pre-fetched
    properties = Property.objects.filter(is_active=True).prefetch_related('images')
    return render(request, "properties/property_list.html", {
        "title": "Properties",
        "properties": properties
    })


@login_required
def landlord_dashboard(request):
    return render(request, "users/dashboard.html", {"title": "Landlord Dashboard"})


@login_required
def tenant_dashboard(request):
    return render(request, "users/dashboard.html", {"title": "Tenant Dashboard"})


@login_required
def add_property(request):
    """Add a new property"""
    if request.user.role not in ['ADMIN', 'LANDLORD', 'PROPERTY_MANAGER']:
        return HttpResponseForbidden("You don't have permission to add properties.")
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, user=request.user)
        image_form = PropertyImageForm(request.POST, request.FILES)
        
        if form.is_valid():
            property_obj = form.save(commit=False)
            
            # Set owner and manager based on user role
            if request.user.role == 'LANDLORD':
                property_obj.owner = request.user
            elif request.user.role == 'PROPERTY_MANAGER':
                property_obj.manager = request.user
            
            property_obj.save()
            form.save_m2m()  # Save many-to-many relationships
            
            # Handle image upload if provided
            if image_form.is_valid() and request.FILES.get('image'):
                image = image_form.save(commit=False)
                image.property = property_obj
                image.save()
            
            messages.success(request, f'Property "{property_obj.name}" added successfully!')
            return redirect('properties:property_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm(user=request.user)
        image_form = PropertyImageForm()
    
    return render(request, 'properties/add_property.html', {
        'form': form,
        'image_form': image_form,
        'title': 'Add Property'
    })


@login_required
def add_rental_unit(request):
    """Add a new rental unit"""
    if request.user.role not in ['ADMIN', 'LANDLORD', 'PROPERTY_MANAGER']:
        return HttpResponseForbidden("You don't have permission to add rental units.")
    
    if request.method == 'POST':
        form = RentalUnitForm(request.POST, user=request.user)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Rental unit "{unit.unit_number}" added successfully!')
            return redirect('properties:property_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RentalUnitForm(user=request.user)
    
    return render(request, 'properties/add_rental_unit.html', {
        'form': form,
        'title': 'Add Rental Unit'
    })


@login_required
def add_amenity(request):
    """Add a new amenity"""
    if request.user.role not in ['ADMIN', 'PROPERTY_MANAGER']:
        return HttpResponseForbidden("You don't have permission to add amenities.")
    
    if request.method == 'POST':
        form = AmenityForm(request.POST)
        if form.is_valid():
            amenity = form.save()
            messages.success(request, f'Amenity "{amenity.name}" added successfully!')
            return redirect('properties:property_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AmenityForm()
    
    return render(request, 'properties/add_amenity.html', {
        'form': form,
        'title': 'Add Amenity'
    })


def property_detail(request, property_id):
    """Display detailed information about a specific property"""
    property_obj = get_object_or_404(Property, id=property_id, is_active=True)
    
    # Get all units for this property
    units = property_obj.units.all().order_by('floor_number', 'unit_number')
    
    # Get amenities
    amenities = property_obj.amenities.all()
    
    # Get images
    images = property_obj.images.all().order_by('-is_primary', 'created_at')
    
    # Check if current user can reserve units
    can_reserve = request.user.is_authenticated and request.user.role == 'TENANT'
    
    context = {
        'property': property_obj,
        'units': units,
        'amenities': amenities,
        'images': images,
        'can_reserve': can_reserve,
        'title': property_obj.name
    }
    
    return render(request, 'properties/property_detail.html', context)


@login_required
def reserve_unit(request, unit_id):
    """Reserve a rental unit (tenant only)"""
    if request.user.role != 'TENANT':
        return HttpResponseForbidden("Only tenants can reserve units.")
    
    unit = get_object_or_404(RentalUnit, id=unit_id)
    
    # Check if unit can be reserved
    if not unit.can_be_reserved():
        messages.error(request, 'This unit is not available for reservation.')
        return redirect('properties:property_detail', property_id=unit.property.id)
    
    # Check if user already has a pending reservation
    existing_reservation = UnitReservation.objects.filter(
        tenant=request.user,
        status__in=['pending', 'paid']
    ).first()
    
    if existing_reservation:
        messages.warning(request, f'You already have a pending reservation for {existing_reservation.unit}. Please complete or cancel it first.')
        return redirect('properties:reservation_detail', reservation_id=existing_reservation.id)
    
    if request.method == 'POST':
        form = UnitReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.unit = unit
            reservation.tenant = request.user
            reservation.expires_at = timezone.now() + timedelta(hours=24)
            reservation.save()
            
            messages.success(request, f'Unit {unit.unit_number} reserved successfully! You have 24 hours to pay the security deposit.')
            return redirect('properties:reservation_detail', reservation_id=reservation.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UnitReservationForm()
    
    return render(request, 'properties/reserve_unit.html', {
        'form': form,
        'unit': unit,
        'title': f'Reserve {unit.unit_number}'
    })


@login_required
def reservation_detail(request, reservation_id):
    """Display reservation details and payment options"""
    reservation = get_object_or_404(UnitReservation, id=reservation_id)
    
    # Check if user owns this reservation
    if reservation.tenant != request.user:
        return HttpResponseForbidden("You can only view your own reservations.")
    
    # Check if reservation has expired
    if reservation.is_expired() and reservation.status == 'pending':
        messages.warning(request, 'Your reservation has expired. Please make a new reservation.')
        return redirect('properties:property_detail', property_id=reservation.unit.property.id)
    
    context = {
        'reservation': reservation,
        'unit': reservation.unit,
        'property': reservation.unit.property,
        'title': f'Reservation Details - {reservation.unit.unit_number}'
    }
    
    return render(request, 'properties/reservation_detail.html', context)


@login_required
def payment_redirect(request, reservation_id):
    """Redirect to payment system for security deposit"""
    reservation = get_object_or_404(UnitReservation, id=reservation_id)
    
    # Check if user owns this reservation
    if reservation.tenant != request.user:
        return HttpResponseForbidden("You can only pay for your own reservations.")
    
    # Check if reservation can still be paid
    if not reservation.can_pay_deposit():
        messages.error(request, 'This reservation cannot be paid for.')
        return redirect('properties:reservation_detail', reservation_id=reservation.id)
    
    # Redirect to payment system with reservation details
    payment_data = {
        'amount': float(reservation.unit.deposit_amount),
        'currency': 'KES',
        'description': f'Security deposit for {reservation.unit}',
        'reference': f'RES_{reservation.id}',
        'reservation_id': reservation.id,
        'return_url': request.build_absolute_uri(
            reverse('properties:payment_success', args=[reservation.id])
        ),
        'cancel_url': request.build_absolute_uri(
            reverse('properties:reservation_detail', args=[reservation.id])
        )
    }
    
    # For now, redirect to a payment form
    # In production, this would redirect to your payment gateway
    return render(request, 'properties/payment_form.html', {
        'payment_data': payment_data,
        'reservation': reservation,
        'title': 'Pay Security Deposit'
    })


@login_required
def payment_success(request, reservation_id):
    """Handle successful payment callback"""
    reservation = get_object_or_404(UnitReservation, id=reservation_id)
    
    # Check if user owns this reservation
    if reservation.tenant != request.user:
        return HttpResponseForbidden("You can only access your own reservations.")
    
    # Update reservation status
    payment_reference = request.GET.get('reference', f'PAY_{reservation.id}_{int(timezone.now().timestamp())}')
    reservation.confirm_payment(payment_reference)
    
    messages.success(request, 'Security deposit paid successfully! Your reservation is now confirmed.')
    return redirect('properties:reservation_detail', reservation_id=reservation.id)


@login_required
def cancel_reservation(request, reservation_id):
    """Cancel a reservation"""
    reservation = get_object_or_404(UnitReservation, id=reservation_id)
    
    # Check if user owns this reservation
    if reservation.tenant != request.user:
        return HttpResponseForbidden("You can only cancel your own reservations.")
    
    # Check if reservation can be cancelled
    if reservation.status not in ['pending', 'paid']:
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('properties:reservation_detail', reservation_id=reservation.id)
    
    if request.method == 'POST':
        reservation.cancel_reservation()
        messages.success(request, 'Reservation cancelled successfully.')
        return redirect('properties:property_detail', property_id=reservation.unit.property.id)
    
    return render(request, 'properties/cancel_reservation.html', {
        'reservation': reservation,
        'title': 'Cancel Reservation'
    })


@login_required
def available_units(request):
    """View for tenants to see available units they can reserve"""
    if request.user.role != 'TENANT':
        return HttpResponseForbidden("Only tenants can view available units.")
    
    # Get all available units that can be reserved
    available_units = RentalUnit.objects.filter(
        is_available=True,
        current_tenant__isnull=True
    ).exclude(
        reservations__status__in=['pending', 'paid', 'confirmed']
    ).select_related('property').prefetch_related('property__images')
    
    # Group units by property for better organization
    properties_with_units = {}
    for unit in available_units:
        property_obj = unit.property
        if property_obj.id not in properties_with_units:
            properties_with_units[property_obj.id] = {
                'property': property_obj,
                'units': []
            }
        properties_with_units[property_obj.id]['units'].append(unit)
    
    context = {
        'properties_with_units': properties_with_units,
        'title': 'Available Units for Reservation'
    }
    
    return render(request, 'properties/available_units.html', context)


@login_required
def make_rental_payment(request, unit_id):
    """View for tenants to make rental payments"""
    if request.user.role != 'TENANT':
        return HttpResponseForbidden("Only tenants can make rental payments.")
    
    unit = get_object_or_404(RentalUnit, id=unit_id)
    
    # Check if tenant has access to this unit
    if unit.current_tenant != request.user:
        messages.error(request, "You can only make payments for units you occupy.")
        return redirect('properties:available_units')
    
    if request.method == 'POST':
        # Handle payment form submission
        payment_method = request.POST.get('payment_method')
        months_paid = int(request.POST.get('months_paid', 1))
        amount = unit.rent_amount * months_paid
        
        # Create payment record
        from payments.models import Payment
        payment = Payment.objects.create(
            tenant=request.user,
            rental_unit=unit,
            property=unit.property,
            payment_type='rent',
            payment_method=payment_method,
            amount=amount,
            months_paid_for=months_paid,
            notes=f"Rent payment for {months_paid} month(s)"
        )
        
        messages.success(request, f'Payment of KES {amount:,.2f} has been recorded successfully!')
        return redirect('payments:view_payments')
    
    context = {
        'unit': unit,
        'title': f'Make Rental Payment - {unit.unit_number}'
    }
    
    return render(request, 'properties/make_rental_payment.html', context)

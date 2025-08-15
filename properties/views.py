from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Property, RentalUnit, Amenity, PropertyImage
from .forms import PropertyForm, RentalUnitForm, AmenityForm, PropertyImageForm
from users.models import Role


def property_list(request):
    from .models import Property
    properties = Property.objects.filter(is_active=True)
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
    """View for adding a new property"""
    # Check if user has permission to add properties
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to add properties.")
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, user=request.user)
        if form.is_valid():
            property = form.save(commit=False)
            # Set the owner to the current user if not already set
            if not property.owner_id:
                property.owner = request.user
            property.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Property added successfully!')
            return redirect('properties:property_list')
    else:
        form = PropertyForm(user=request.user)
    
    # Add image form for property images
    image_form = PropertyImageForm()
    
    return render(request, 'properties/add_property.html', {
        'form': form,
        'image_form': image_form,
        'title': 'Add Property'
    })


@login_required
def add_rental_unit(request):
    """View for adding a new rental unit"""
    # Check if user has permission to add rental units
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to add rental units.")
    
    if request.method == 'POST':
        form = RentalUnitForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rental unit added successfully!')
            return redirect('properties:property_list')
    else:
        form = RentalUnitForm(user=request.user)
    
    return render(request, 'properties/add_rental_unit.html', {
        'form': form,
        'title': 'Add Rental Unit'
    })


@login_required
def add_amenity(request):
    """View for adding a new amenity"""
    # Check if user has permission to add amenities
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to add amenities.")
    
    if request.method == 'POST':
        form = AmenityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Amenity added successfully!')
            return redirect('properties:property_list')
    else:
        form = AmenityForm()
    
    return render(request, 'properties/add_amenity.html', {
        'form': form,
        'title': 'Add Amenity'
    })

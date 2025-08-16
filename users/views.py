from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.http import HttpResponseForbidden
from django.db.models import Q
from .models import CustomUser, UserProfile, Role
from .forms import CustomUserCreationForm, UserProfileForm, CustomAuthenticationForm, TenantCreationForm
from properties.models import Property, RentalUnit


class CustomLoginView(LoginView):
    """Custom login view with role-based redirection"""
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure accessing the login page signs out any currently authenticated user
        if request.method == 'GET' and request.user.is_authenticated:
            logout(request)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        """Redirect based on user role"""
        user = self.request.user
        if hasattr(user, 'role') and user.role == Role.ADMIN:
            return reverse_lazy('admin:index')
        # All other roles go to the in-app dashboard
        return reverse_lazy('users:dashboard')


def custom_logout_view(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('users:login')


class UserRegistrationView(CreateView):
    """User registration view with role assignment"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        """Process valid registration form"""
        response = super().form_valid(form)
        
        # Create user profile only if it doesn't exist
        UserProfile.objects.get_or_create(user=self.object)
        
        # Log the user in
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        
        if user:
            login(self.request, user)
            messages.success(
                self.request, 
                f'Welcome {user.first_name or user.username}! Your account has been created successfully.'
            )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Account'
        return context


class UserProfileView(LoginRequiredMixin, UpdateView):
    """User profile view for updating profile information"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self, queryset=None):
        """Get or create user profile"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        """Process valid profile form"""
        response = super().form_valid(form)
        messages.success(self.request, 'Your profile has been updated successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Profile'
        context['user'] = self.request.user
        return context


@login_required
def dashboard_view(request):
    """Dashboard view with role-based content"""
    user = request.user
    context = {
        'user': user,
        'title': 'Dashboard'
    }
    
    if hasattr(user, 'role'):
        if user.role == Role.ADMIN:
            # Admin dashboard - redirect to admin interface
            return redirect('admin:index')
        elif user.role == Role.PROPERTY_MANAGER:
            # Property manager dashboard
            properties = user.get_accessible_properties()
            context.update({
                'properties': properties,
                'properties_count': properties.count(),
                'role_display': 'Property Manager'
            })
            return render(request, 'users/property_manager_dashboard.html', context)
        elif user.role == Role.LANDLORD:
            # Landlord dashboard
            properties = user.get_accessible_properties()
            context.update({
                'properties': properties,
                'properties_count': properties.count(),
                'role_display': 'Landlord'
            })
            return render(request, 'users/landlord_dashboard.html', context)
        elif user.role == Role.TENANT:
            # Tenant dashboard
            from properties.models import RentalUnit
            rental_units = RentalUnit.objects.filter(current_tenant=user)
            context.update({
                'rental_units': rental_units,
                'rental_units_count': rental_units.count(),
                'role_display': 'Tenant'
            })
            return render(request, 'users/tenant_dashboard.html', context)
    
    # Default dashboard
    return render(request, 'users/dashboard.html', context)


@login_required
def add_tenant(request):
    """Add a new tenant (admin, property manager, landlord only)"""
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to add tenants.")
    
    if request.method == 'POST':
        form = TenantCreationForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # Set who created this user
            user.created_by = request.user
            user.save()
            
            # Set the creator relationship based on role
            if request.user.role == Role.ADMIN:
                # Admin can create any user type
                pass
            elif request.user.role == Role.PROPERTY_MANAGER:
                # Property managers can only create tenants
                if user.role != Role.TENANT:
                    messages.error(request, 'Property managers can only create tenant accounts.')
                    return redirect('users:add_tenant')
            elif request.user.role == Role.LANDLORD:
                # Landlords can only create tenants
                if user.role != Role.TENANT:
                    messages.error(request, 'Landlords can only create tenant accounts.')
                    return redirect('users:add_tenant')
            
            messages.success(request, f'User "{user.username}" added successfully!')
            return redirect('users:tenant_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TenantCreationForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Add New User',
        'user_role': request.user.role
    }
    
    return render(request, 'users/add_tenant.html', context)


@login_required
def tenant_list(request):
    """View list of tenants based on user permissions"""
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to view tenant lists.")
    
    # Get tenants based on user role and permissions
    if request.user.role == Role.ADMIN:
        # Admin can see all users
        tenants = CustomUser.objects.all().order_by('-created_at')
        context_title = "All Registered Users"
    elif request.user.role == Role.PROPERTY_MANAGER:
        # Property managers see tenants in properties they manage
        managed_properties = Property.objects.filter(manager=request.user)
        tenant_ids = RentalUnit.objects.filter(
            property__in=managed_properties
        ).values_list('current_tenant_id', flat=True).distinct()
        
        # Also include tenants created by this property manager
        tenants = CustomUser.objects.filter(
            Q(id__in=tenant_ids) | Q(created_by=request.user)
        ).order_by('-created_at')
        context_title = "Tenants in Managed Properties"
    elif request.user.role == Role.LANDLORD:
        # Landlords see tenants in properties they own
        owned_properties = Property.objects.filter(owner=request.user)
        tenant_ids = RentalUnit.objects.filter(
            property__in=owned_properties
        ).values_list('current_tenant_id', flat=True).distinct()
        
        # Also include tenants created by this landlord
        tenants = CustomUser.objects.filter(
            Q(id__in=tenant_ids) | Q(created_by=request.user)
        ).order_by('-created_at')
        context_title = "Tenants in Owned Properties"
    else:
        tenants = CustomUser.objects.none()
        context_title = "No Access"
    
    # Add additional context for each tenant
    for tenant in tenants:
        if tenant.role == Role.TENANT:
            # Get current rental units for tenants
            tenant.current_units = RentalUnit.objects.filter(current_tenant=tenant)
            tenant.total_units = tenant.current_units.count()
        else:
            tenant.current_units = []
            tenant.total_units = 0
    
    context = {
        'tenants': tenants,
        'title': context_title,
        'user_role': request.user.role
    }
    
    return render(request, 'users/tenant_list.html', context)


@login_required
def tenant_detail(request, tenant_id):
    """View detailed information about a specific tenant"""
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to view tenant details.")
    
    tenant = get_object_or_404(CustomUser, id=tenant_id)
    
    # Check if user has permission to view this tenant
    can_view = False
    if request.user.role == Role.ADMIN:
        can_view = True
    elif request.user.role == Role.PROPERTY_MANAGER:
        # Check if tenant is in properties managed by this user
        managed_properties = Property.objects.filter(manager=request.user)
        can_view = RentalUnit.objects.filter(
            property__in=managed_properties,
            current_tenant=tenant
        ).exists()
    elif request.user.role == Role.LANDLORD:
        # Check if tenant is in properties owned by this user
        owned_properties = Property.objects.filter(owner=request.user)
        can_view = RentalUnit.objects.filter(
            property__in=owned_properties,
            current_tenant=tenant
        ).exists()
    
    if not can_view:
        return HttpResponseForbidden("You don't have permission to view this tenant.")
    
    # Get tenant's current rental units
    current_units = RentalUnit.objects.filter(current_tenant=tenant)
    
    # Get tenant's reservation history
    reservations = tenant.unit_reservations.all().order_by('-reservation_date')
    
    context = {
        'tenant': tenant,
        'current_units': current_units,
        'reservations': reservations,
        'title': f'Tenant Details - {tenant.get_full_name()}'
    }
    
    return render(request, 'users/tenant_detail.html', context)

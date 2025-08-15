from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from .models import CustomUser, UserProfile, Role
from .forms import CustomUserCreationForm, UserProfileForm, CustomAuthenticationForm


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
    """View for adding a new tenant"""
    # Check if user has permission to add tenants
    if request.user.role not in [Role.ADMIN, Role.PROPERTY_MANAGER, Role.LANDLORD]:
        return HttpResponseForbidden("You don't have permission to add tenants.")
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        # Set the role to tenant for all added users
        if form.is_valid():
            user = form.save(commit=False)
            user.role = Role.TENANT
            user.save()
            
            # Create user profile
            UserProfile.objects.get_or_create(user=user)
            
            messages.success(request, 'Tenant added successfully!')
            return redirect('users:dashboard')
    else:
        form = CustomUserCreationForm()
        # Hide the role field since it's always tenant
        form.fields['role'].widget = forms.HiddenInput()
        form.fields['role'].initial = Role.TENANT
    
    return render(request, 'users/add_tenant.html', {
        'form': form,
        'title': 'Add Tenant'
    })

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from .models import CustomUser, UserProfile, Role


class TenantCreationForm(forms.ModelForm):
    """Form for admins, property managers, and landlords to add tenants"""
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Enter a secure password"
    )
    
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Enter the same password as before, for verification"
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'role'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254712345678 or 0712345678'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'role': 'User Role'
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'email': 'Required. Enter a valid email address.',
            'first_name': 'Required. Enter the first name.',
            'last_name': 'Required. Enter the last name.',
            'phone_number': 'Enter phone number in format: +254712345678 or 0712345678',
            'role': 'Select the role for this user'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial role to TENANT
        self.fields['role'].initial = Role.TENANT
        
        # Filter role choices based on user permissions
        if user:
            if user.role == Role.ADMIN:
                # Admin can create any role
                self.fields['role'].choices = [
                    (Role.TENANT, 'Tenant'),
                    (Role.LANDLORD, 'Landlord'),
                    (Role.PROPERTY_MANAGER, 'Property Manager'),
                    (Role.ADMIN, 'Administrator')
                ]
            elif user.role == Role.PROPERTY_MANAGER:
                # Property managers can only create tenants
                self.fields['role'].choices = [(Role.TENANT, 'Tenant')]
                self.fields['role'].initial = Role.TENANT
                self.fields['role'].widget.attrs['readonly'] = True
            elif user.role == Role.LANDLORD:
                # Landlords can only create tenants
                self.fields['role'].choices = [(Role.TENANT, 'Tenant')]
                self.fields['role'].initial = Role.TENANT
                self.fields['role'].widget.attrs['readonly'] = True
            else:
                # Other users cannot create accounts
                self.fields['role'].choices = []
    
    def clean_password2(self):
        """Validate that both passwords match"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_username(self):
        """Validate username uniqueness"""
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username
    
    def clean_phone_number(self):
        """Validate phone number format and uniqueness"""
        phone_number = self.cleaned_data.get('phone_number')
        
        # Normalize phone number format
        if phone_number.startswith('07') or phone_number.startswith('01'):
            phone_number = '+254' + phone_number[1:]
        
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("A user with this phone number already exists.")
        
        return phone_number
    
    def save(self, commit=True):
        """Save the user with the provided password"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields"""
    
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address."
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Required. Enter your first name."
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Required. Enter your last name."
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        help_text="Enter phone number in format: +254712345678 or 0712345678"
    )
    
    role = forms.ChoiceField(
        choices=[(Role.TENANT, 'Tenant'), (Role.LANDLORD, 'Landlord'), (Role.PROPERTY_MANAGER, 'Property Manager')],
        initial=Role.TENANT,
        help_text="Select your role in the system"
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the Terms and Conditions"
    )
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'role', 'password1', 'password2'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'phone_number',
            'role',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'terms_accepted',
            Submit('submit', 'Create Account', css_class='btn btn-orange w-full')
        )
        
        # Add CSS classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'terms_accepted':
                field.widget.attrs['class'] = 'form-check-input'
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_phone_number(self):
        """Validate phone number format and uniqueness"""
        phone_number = self.cleaned_data.get('phone_number')
        
        # Normalize phone number format
        if phone_number.startswith('07') or phone_number.startswith('01'):
            phone_number = '+254' + phone_number[1:]
        
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("A user with this phone number already exists.")
        
        return phone_number
    
    def save(self, commit=True):
        """Save user with normalized phone number"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with enhanced styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            HTML('<div class="form-check mb-3">'
                 '<input type="checkbox" class="form-check-input" id="remember_me" name="remember_me">'
                 '<label class="form-check-label" for="remember_me">Remember me</label>'
                 '</div>'),
            Submit('submit', 'Sign In', css_class='btn btn-orange w-full')
        )
        
        # Add CSS classes and placeholders
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username or Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    # Add user fields that can be updated
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 'national_id', 'county', 'town', 'address',
            'emergency_contact_name', 'emergency_contact_phone',
            'preferred_language', 'email_notifications', 'sms_notifications'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-populate user fields if instance exists
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone_number'].initial = self.instance.user.phone_number
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3">Personal Information</h5>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('date_of_birth', css_class='form-group col-md-6 mb-3'),
                Column('national_id', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<h5 class="mb-3 mt-4">Address Information</h5>'),
            Row(
                Column('county', css_class='form-group col-md-6 mb-3'),
                Column('town', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'address',
            
            HTML('<h5 class="mb-3 mt-4">Emergency Contact</h5>'),
            Row(
                Column('emergency_contact_name', css_class='form-group col-md-6 mb-3'),
                Column('emergency_contact_phone', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<h5 class="mb-3 mt-4">Preferences</h5>'),
            Row(
                Column('preferred_language', css_class='form-group col-md-4 mb-3'),
                Column('email_notifications', css_class='form-group col-md-4 mb-3'),
                Column('sms_notifications', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            
            Submit('submit', 'Update Profile', css_class='btn btn-orange')
        )
        
        # Add CSS classes to form fields
        for field_name, field in self.fields.items():
            if field_name in ['email_notifications', 'sms_notifications']:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        """Save profile and update related user fields"""
        profile = super().save(commit=False)
        
        # Update user fields
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            profile.user.email = self.cleaned_data.get('email', '')
            profile.user.phone_number = self.cleaned_data.get('phone_number', '')
            
            if commit:
                profile.user.save()
        
        if commit:
            profile.save()
        
        return profile
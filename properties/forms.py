from django import forms
from .models import Property, RentalUnit, Amenity, PropertyImage
from users.models import CustomUser
from decimal import Decimal
from .models import UnitReservation


class PropertyForm(forms.ModelForm):
    """Form for adding/editing properties"""
    
    class Meta:
        model = Property
        fields = [
            'name', 'address', 'county', 'town', 'property_type', 'description',
            'number_of_floors', 'units_per_floor', 'contact_phone', 'contact_email', 
            'amenities', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'county': forms.Select(attrs={'class': 'form-control'}),
            'town': forms.TextInput(attrs={'class': 'form-control'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'number_of_floors': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'units_per_floor': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'amenities': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Only show amenities that are available
            self.fields['amenities'].queryset = Amenity.objects.all()
            # Set the owner to the current user
            # if not self.instance.pk:  # Only for new properties
            #     self.fields['owner'].initial = user
            #     self.fields['owner'].widget = forms.HiddenInput()
        
        # Make commercial fields required when property type is commercial
        self.fields['number_of_floors'].required = False
        self.fields['units_per_floor'].required = False
        
        # Add JavaScript to show/hide commercial fields based on property type
        self.fields['property_type'].widget.attrs.update({
            'onchange': 'toggleCommercialFields(this.value)'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        property_type = cleaned_data.get('property_type')
        number_of_floors = cleaned_data.get('number_of_floors')
        units_per_floor = cleaned_data.get('units_per_floor')
        
        if property_type == 'commercial':
            if not number_of_floors:
                self.add_error('number_of_floors', 'Number of floors is required for commercial properties.')
            if not units_per_floor:
                self.add_error('units_per_floor', 'Units per floor is required for commercial properties.')
            
            if number_of_floors and number_of_floors < 1:
                self.add_error('number_of_floors', 'Number of floors must be at least 1.')
            if units_per_floor and units_per_floor < 1:
                self.add_error('units_per_floor', 'Units per floor must be at least 1.')
        
        return cleaned_data


class RentalUnitForm(forms.ModelForm):
    """Form for adding/editing rental units"""
    
    class Meta:
        model = RentalUnit
        fields = [
            'property', 'unit_number', 'unit_type', 'rent_amount', 'deposit_amount', 
            'floor_number', 'floor_area', 'is_available', 'current_tenant',
            'lease_start_date', 'lease_end_date', 'description'
        ]
        widgets = {
            'property': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'updateFloorChoices(this.value)'
            }),
            'unit_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A101, Ground-01'
            }),
            'unit_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Describe the unit features, amenities, etc.'
            }),
            'rent_amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'deposit_amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'readonly': 'readonly',
                'placeholder': 'Auto-calculated'
            }),
            'floor_number': forms.Select(attrs={
                'class': 'form-control'
            }),
            'floor_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'current_tenant': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lease_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'lease_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'property': 'Property',
            'unit_number': 'Unit Number',
            'unit_type': 'Unit Type',
            'rent_amount': 'Monthly Rent (KES)',
            'deposit_amount': 'Security Deposit (KES)',
            'floor_number': 'Floor Number',
            'floor_area': 'Floor Area (sq ft)',
            'is_available': 'Unit Available',
            'current_tenant': 'Current Tenant',
            'lease_start_date': 'Lease Start Date',
            'lease_end_date': 'Lease End Date',
            'description': 'Description'
        }
        help_texts = {
            'property': 'Select the property where this unit will be located',
            'unit_number': 'Enter a unique identifier for this unit (e.g., A101, Ground-01)',
            'unit_type': 'Choose the type of rental unit',
            'rent_amount': 'Enter the monthly rent amount in Kenyan Shillings',
            'deposit_amount': 'Security deposit is automatically calculated as 113% of monthly rent',
            'floor_number': 'Select the floor number (required for commercial properties)',
            'floor_area': 'Enter the floor area in square feet',
            'is_available': 'Check if the unit is currently available for rent',
            'current_tenant': 'Select the current tenant if the unit is occupied',
            'lease_start_date': 'Enter the start date of the lease agreement',
            'lease_end_date': 'Enter the end date of the lease agreement',
            'description': 'Describe the unit features, amenities, and any special characteristics'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter properties based on user role
        if user:
            if user.role == 'ADMIN':
                # Admin can see all properties
                self.fields['property'].queryset = Property.objects.filter(is_active=True)
            elif user.role == 'LANDLORD':
                # Landlords can only see their own properties
                self.fields['property'].queryset = Property.objects.filter(owner=user, is_active=True)
            elif user.role == 'PROPERTY_MANAGER':
                # Property managers can see properties they manage
                self.fields['property'].queryset = Property.objects.filter(manager=user, is_active=True)
            else:
                # Other users see no properties
                self.fields['property'].queryset = Property.objects.none()
        
        # Only show tenants who are tenants
        self.fields['current_tenant'].queryset = CustomUser.objects.filter(role='TENANT')
        
        # Set help text for deposit amount
        self.fields['deposit_amount'].help_text = "Security deposit: 113% of monthly rent (auto-calculated)"
        
        # Initialize floor number choices
        self.fields['floor_number'].choices = [('', 'Select Floor')]
        
        # Set initial floor choices if property is already selected and instance exists
        if hasattr(self, 'instance') and self.instance and self.instance.pk and self.instance.property:
            self.update_floor_choices(self.instance.property)
    
    def update_floor_choices(self, property):
        """Update floor number choices based on selected property"""
        if property and property.is_commercial():
            floor_choices = [('', 'Select Floor')]
            for i in range(1, property.number_of_floors + 1):
                if i == 1:
                    floor_choices.append((i, 'Ground Floor'))
                elif i == 2:
                    floor_choices.append((i, '1st Floor'))
                elif i == 3:
                    floor_choices.append((i, '2nd Floor'))
                else:
                    floor_choices.append((i, f'{i-1}rd Floor'))
            self.fields['floor_number'].choices = floor_choices
            self.fields['floor_number'].required = True
        else:
            self.fields['floor_number'].choices = [('', 'Not Applicable')]
            self.fields['floor_number'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        rent_amount = cleaned_data.get('rent_amount')
        property = cleaned_data.get('property')
        floor_number = cleaned_data.get('floor_number')
        lease_start_date = cleaned_data.get('lease_start_date')
        lease_end_date = cleaned_data.get('lease_end_date')
        
        if rent_amount:
            # Calculate security deposit as 113% of monthly rent
            deposit_amount = rent_amount * Decimal('1.13')
            cleaned_data['deposit_amount'] = deposit_amount
        
        # Validate floor number for commercial properties
        if property and property.is_commercial():
            if not floor_number:
                self.add_error('floor_number', 'Floor number is required for commercial properties.')
            elif floor_number > property.number_of_floors:
                self.add_error('floor_number', f'Floor number cannot exceed {property.number_of_floors}.')
        
        # Validate lease dates
        if lease_start_date and lease_end_date:
            if lease_start_date >= lease_end_date:
                self.add_error('lease_end_date', 'Lease end date must be after lease start date.')
        
        # Validate unit number uniqueness within the same property
        unit_number = cleaned_data.get('unit_number')
        if unit_number and property:
            existing_units = RentalUnit.objects.filter(
                property=property, 
                unit_number=unit_number
            )
            if self.instance.pk:
                existing_units = existing_units.exclude(pk=self.instance.pk)
            
            if existing_units.exists():
                self.add_error('unit_number', f'A unit with number "{unit_number}" already exists in this property.')
        
        return cleaned_data


class AmenityForm(forms.ModelForm):
    """Form for adding/editing amenities"""
    
    class Meta:
        model = Amenity
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PropertyImageForm(forms.ModelForm):
    """Form for uploading property images"""
    class Meta:
        model = PropertyImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': False
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image caption (optional)'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field not required since it's optional
        self.fields['image'].required = False


class UnitReservationForm(forms.ModelForm):
    """Form for tenants to reserve rental units"""
    
    class Meta:
        model = UnitReservation
        fields = ['intended_move_in_date', 'notes']
        widgets = {
            'intended_move_in_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': 'today'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requirements or notes for your reservation...'
            }),
        }
        labels = {
            'intended_move_in_date': 'Intended Move-in Date',
            'notes': 'Additional Notes'
        }
        help_texts = {
            'intended_move_in_date': 'When do you plan to move into this unit?',
            'notes': 'Any special requirements or additional information for your reservation'
        }
    
    def clean_intended_move_in_date(self):
        """Validate that move-in date is in the future"""
        from django.utils import timezone
        from datetime import date
        
        move_in_date = self.cleaned_data.get('intended_move_in_date')
        if move_in_date and move_in_date <= date.today():
            raise forms.ValidationError("Move-in date must be in the future.")
        return move_in_date
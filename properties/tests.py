from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Property, RentalUnit, PropertyImage, Amenity

User = get_user_model()


class PropertyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )
        self.amenity = Amenity.objects.create(
            name='Swimming Pool',
            description='Pool facility'
        )

    def test_property_creation(self):
        """Test property model creation with Kenya-specific fields"""
        property = Property.objects.create(
            name='Test Apartments',
            address='123 Test Street',
            county='nairobi',
            town='Westlands',
            property_type='apartment',
            owner=self.user,
            contact_phone='+254712345678',
            contact_email='contact@test.com'
        )
        property.amenities.add(self.amenity)
        
        self.assertEqual(property.name, 'Test Apartments')
        self.assertEqual(property.county, 'nairobi')
        self.assertEqual(property.get_county_display(), 'Nairobi')
        self.assertEqual(property.property_type, 'apartment')
        self.assertTrue(property.is_active)
        self.assertEqual(property.amenities.count(), 1)
        self.assertEqual(str(property), 'Test Apartments - Westlands, Nairobi')

    def test_rental_unit_creation(self):
        """Test rental unit model with enhanced fields"""
        property = Property.objects.create(
            name='Test Property',
            address='Test Address',
            county='nairobi',
            town='CBD',
            property_type='apartment',
            owner=self.user
        )
        
        unit = RentalUnit.objects.create(
            property=property,
            unit_number='A101',
            unit_type='2br',
            rent_amount=Decimal('50000.00'),
            deposit_amount=Decimal('100000.00'),
            floor_area=800,
            floor_number=1
        )
        
        self.assertEqual(unit.unit_number, 'A101')
        self.assertEqual(unit.rent_amount, Decimal('50000.00'))
        self.assertEqual(unit.get_rent_display(), 'KES 50,000.00')
        self.assertEqual(unit.get_deposit_display(), 'KES 100,000.00')
        self.assertTrue(unit.is_available)
        self.assertFalse(unit.is_occupied())

    def test_property_unit_counts(self):
        """Test property unit counting methods"""
        property = Property.objects.create(
            name='Test Property',
            address='Test Address',
            county='nairobi',
            town='CBD',
            property_type='apartment',
            owner=self.user
        )
        
        # Create units
        RentalUnit.objects.create(
            property=property,
            unit_number='A101',
            unit_type='1br',
            rent_amount=Decimal('30000.00'),
            deposit_amount=Decimal('60000.00'),
            is_available=True
        )
        RentalUnit.objects.create(
            property=property,
            unit_number='A102',
            unit_type='2br',
            rent_amount=Decimal('45000.00'),
            deposit_amount=Decimal('90000.00'),
            is_available=False
        )
        
        self.assertEqual(property.get_total_units_count(), 2)
        self.assertEqual(property.get_available_units_count(), 1)

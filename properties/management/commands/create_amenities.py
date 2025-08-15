from django.core.management.base import BaseCommand
from properties.models import Amenity


class Command(BaseCommand):
    help = 'Create initial amenities for properties'

    def handle(self, *args, **options):
        amenities_data = [
            {'name': 'Swimming Pool', 'description': 'Swimming pool facility', 'icon': '🏊'},
            {'name': 'Gym/Fitness Center', 'description': 'Fitness and workout facilities', 'icon': '💪'},
            {'name': 'Parking', 'description': 'Dedicated parking space', 'icon': '🚗'},
            {'name': 'Security', 'description': '24/7 security services', 'icon': '🔒'},
            {'name': 'Generator/Backup Power', 'description': 'Backup power supply', 'icon': '⚡'},
            {'name': 'Water Supply', 'description': 'Reliable water supply', 'icon': '💧'},
            {'name': 'Internet/WiFi', 'description': 'Internet connectivity', 'icon': '📶'},
            {'name': 'Elevator', 'description': 'Elevator access', 'icon': '🛗'},
            {'name': 'Balcony', 'description': 'Private balcony', 'icon': '🏠'},
            {'name': 'Garden/Green Space', 'description': 'Garden or green areas', 'icon': '🌳'},
            {'name': 'Laundry', 'description': 'Laundry facilities', 'icon': '👕'},
            {'name': 'Air Conditioning', 'description': 'Air conditioning system', 'icon': '❄️'},
            {'name': 'CCTV Surveillance', 'description': 'CCTV security system', 'icon': '📹'},
            {'name': 'Playground', 'description': 'Children playground', 'icon': '🛝'},
            {'name': 'Shopping Center Nearby', 'description': 'Close to shopping facilities', 'icon': '🛒'},
            {'name': 'Public Transport Access', 'description': 'Easy access to public transport', 'icon': '🚌'},
            {'name': 'Hospital/Clinic Nearby', 'description': 'Close to medical facilities', 'icon': '🏥'},
            {'name': 'School Nearby', 'description': 'Close to educational institutions', 'icon': '🏫'},
        ]

        created_count = 0
        for amenity_data in amenities_data:
            amenity, created = Amenity.objects.get_or_create(
                name=amenity_data['name'],
                defaults={
                    'description': amenity_data['description'],
                    'icon': amenity_data['icon']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created amenity: {amenity.name}")

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} amenities')
        )
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Role


class Command(BaseCommand):
    """Management command to set up Django groups and permissions for role-based access control"""
    
    help = 'Create user groups and assign permissions based on roles'
    
    def handle(self, *args, **options):
        """Create groups and assign permissions"""
        
        self.stdout.write(self.style.SUCCESS('Setting up user groups and permissions...'))
        
        # Define permissions for each role
        role_permissions = {
            Role.ADMIN: {
                'description': 'Full system access',
                'permissions': [
                    # User permissions
                    'users.add_customuser',
                    'users.change_customuser',
                    'users.delete_customuser',
                    'users.view_customuser',
                    'users.add_userprofile',
                    'users.change_userprofile',
                    'users.delete_userprofile',
                    'users.view_userprofile',
                    
                    # Property permissions
                    'properties.add_property',
                    'properties.change_property',
                    'properties.delete_property',
                    'properties.view_property',
                    'properties.add_rentalunit',
                    'properties.change_rentalunit',
                    'properties.delete_rentalunit',
                    'properties.view_rentalunit',
                    
                    # Payment permissions
                    'payments.add_payment',
                    'payments.change_payment',
                    'payments.delete_payment',
                    'payments.view_payment',
                    
                    # Maintenance permissions
                    'maintenance.add_maintenancerequest',
                    'maintenance.change_maintenancerequest',
                    'maintenance.delete_maintenancerequest',
                    'maintenance.view_maintenancerequest',
                    
                    # Report permissions
                    'reports.view_reports',
                    'reports.generate_reports',
                ]
            },
            
            Role.PROPERTY_MANAGER: {
                'description': 'Manage assigned properties and tenants',
                'permissions': [
                    # Limited user permissions
                    'users.view_customuser',
                    'users.change_customuser',  # Only for tenants/landlords
                    
                    # Property permissions
                    'properties.add_property',
                    'properties.change_property',
                    'properties.view_property',
                    'properties.add_rentalunit',
                    'properties.change_rentalunit',
                    'properties.view_rentalunit',
                    
                    # Payment permissions
                    'payments.add_payment',
                    'payments.change_payment',
                    'payments.view_payment',
                    
                    # Maintenance permissions
                    'maintenance.add_maintenancerequest',
                    'maintenance.change_maintenancerequest',
                    'maintenance.view_maintenancerequest',
                    
                    # Report permissions
                    'reports.view_reports',
                ]
            },
            
            Role.LANDLORD: {
                'description': 'Manage owned properties',
                'permissions': [
                    # Limited user permissions
                    'users.view_customuser',  # Only tenants
                    
                    # Property permissions
                    'properties.add_property',
                    'properties.change_property',
                    'properties.view_property',
                    'properties.add_rentalunit',
                    'properties.change_rentalunit',
                    'properties.view_rentalunit',
                    
                    # Payment permissions
                    'payments.view_payment',
                    
                    # Maintenance permissions
                    'maintenance.change_maintenancerequest',
                    'maintenance.view_maintenancerequest',
                    
                    # Report permissions
                    'reports.view_reports',
                ]
            },
            
            Role.TENANT: {
                'description': 'View rental information and make payments',
                'permissions': [
                    # Limited user permissions
                    'users.view_customuser',  # Only self
                    'users.change_userprofile',  # Only own profile
                    
                    # Property permissions (view only)
                    'properties.view_property',
                    'properties.view_rentalunit',
                    
                    # Payment permissions
                    'payments.add_payment',
                    'payments.view_payment',  # Only own payments
                    
                    # Maintenance permissions
                    'maintenance.add_maintenancerequest',
                    'maintenance.view_maintenancerequest',  # Only own requests
                ]
            }
        }
        
        # Create groups and assign permissions
        for role, config in role_permissions.items():
            group, created = Group.objects.get_or_create(name=role)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {role}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Group already exists: {role}')
                )
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions to group
            permissions_added = 0
            for perm_codename in config['permissions']:
                try:
                    app_label, codename = perm_codename.split('.')
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    group.permissions.add(permission)
                    permissions_added += 1
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Permission not found: {perm_codename} (will be added after migrations)'
                        )
                    )
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR(f'Invalid permission format: {perm_codename}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Added {permissions_added} permissions to {role} group'
                )
            )
        
        # Create custom permissions that don't exist yet
        self.create_custom_permissions()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up user groups and permissions!')
        )
    
    def create_custom_permissions(self):
        """Create custom permissions for the application"""
        
        custom_permissions = [
            {
                'app_label': 'reports',
                'model': 'report',
                'codename': 'view_reports',
                'name': 'Can view reports'
            },
            {
                'app_label': 'reports',
                'model': 'report',
                'codename': 'generate_reports',
                'name': 'Can generate reports'
            },
        ]
        
        for perm_data in custom_permissions:
            try:
                content_type, created = ContentType.objects.get_or_create(
                    app_label=perm_data['app_label'],
                    model=perm_data['model']
                )
                
                permission, created = Permission.objects.get_or_create(
                    content_type=content_type,
                    codename=perm_data['codename'],
                    defaults={'name': perm_data['name']}
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created custom permission: {perm_data["codename"]}')
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating permission {perm_data["codename"]}: {e}')
                )
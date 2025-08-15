from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.utils.translation import gettext_lazy as _

from unfold.forms import AdminPasswordChangeForm
from unfold.admin import StackedInline
from unfold.admin import ModelAdmin

from .models import CustomUser, UserProfile, Role
from .forms import CustomUserCreationForm, UserProfileForm


admin.site.unregister(Group)


class UserProfileInline(StackedInline):
    """Inline admin for UserProfile"""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile Information"
    fields = (
        ("date_of_birth", "national_id"),
        ("county", "town"),
        "address",
        ("emergency_contact_name", "emergency_contact_phone"),
        ("preferred_language",),
        ("email_notifications", "sms_notifications"),
    )


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    """Custom user admin with Unfold styling"""

    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    inlines = [UserProfileInline]
    # Fields to display in the user list
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "phone_number",
        "is_active",
        "date_joined",
    )

    # Fields to filter by
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    )

    # Fields to search
    search_fields = ("username", "email", "first_name", "last_name", "phone_number")

    # Ordering
    ordering = ("-date_joined",)

    # Fields for the user detail/edit form
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "phone_number")},
        ),
        (
            _("Role & Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined"), "classes": ("collapse",)},
        ),
    )

    # Fields for adding a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        """Filter users based on current user's role"""
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, "role") and request.user.role == Role.ADMIN:
            return qs
        elif (
            hasattr(request.user, "role") and request.user.role == Role.PROPERTY_MANAGER
        ):
            # Property managers can only see tenants and landlords
            return qs.filter(role__in=[Role.TENANT, Role.LANDLORD])
        else:
            # Other users can only see themselves
            return qs.filter(id=request.user.id)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    """User profile admin with Unfold styling"""

    list_display = (
        "user",
        "county",
        "town",
        "preferred_language",
        "email_notifications",
        "sms_notifications",
    )

    list_filter = (
        "county",
        "preferred_language",
        "email_notifications",
        "sms_notifications",
    )

    search_fields = ("user__username", "user__email", "county", "town", "national_id")

    fieldsets = (
        (_("User"), {"fields": ("user",)}),
        (_("Personal Information"), {"fields": ("date_of_birth", "national_id")}),
        (_("Address"), {"fields": ("county", "town", "address")}),
        (
            _("Emergency Contact"),
            {"fields": ("emergency_contact_name", "emergency_contact_phone")},
        ),
        (
            _("Preferences"),
            {
                "fields": (
                    "preferred_language",
                    "email_notifications",
                    "sms_notifications",
                )
            },
        ),
    )

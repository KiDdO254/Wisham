from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Index → login for convenience
    path('', views.CustomLoginView.as_view(), name='index'),

    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # User profile URLs
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Add tenant URL
    path('add-tenant/', views.add_tenant, name='add_tenant'),
]
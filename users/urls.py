from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.CustomLoginView.as_view(), name='index'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('add-tenant/', views.add_tenant, name='add_tenant'),
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenant/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
]
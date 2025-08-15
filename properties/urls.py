from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('add-property/', views.add_property, name='add_property'),
    path('add-rental-unit/', views.add_rental_unit, name='add_rental_unit'),
    path('add-amenity/', views.add_amenity, name='add_amenity'),
]
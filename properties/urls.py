from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('property/<int:property_id>/', views.property_detail, name='property_detail'),
    path('add-property/', views.add_property, name='add_property'),
    path('add-rental-unit/', views.add_rental_unit, name='add_rental_unit'),
    path('add-amenity/', views.add_amenity, name='add_amenity'),
    
    # Unit Reservation URLs
    path('reserve-unit/<int:unit_id>/', views.reserve_unit, name='reserve_unit'),
    path('reservation/<int:reservation_id>/', views.reservation_detail, name='reservation_detail'),
    path('reservation/<int:reservation_id>/payment/', views.payment_redirect, name='payment_redirect'),
    path('reservation/<int:reservation_id>/payment/success/', views.payment_success, name='payment_success'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    
    # Tenant-specific URLs
    path('available-units/', views.available_units, name='available_units'),
    path('make-rental-payment/<int:unit_id>/', views.make_rental_payment, name='make_rental_payment'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('password-reset/', views.password_reset, name='password_reset'),
    
    path('properties/', views.properties, name='properties'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('landlord/dashboard/', views.landlord_dashboard, name='landlord_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    path('booking/request/', views.booking_request, name='booking_request'),
    path('booking/request/<int:property_id>/', views.booking_request, name='booking_request_property'),
    path('booking/approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    
    path('payment/<int:booking_id>/', views.payment, name='payment'),
    
    path('property/add/', views.add_property, name='add_property'),
    path('property/edit/<int:pk>/', views.edit_property, name='edit_property'),
    path('property/delete/<int:pk>/', views.delete_property, name='delete_property'),
    
    path('maintenance/request/', views.create_maintenance_request, name='maintenance_request'),
    
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    path('user/approve/<int:user_id>/', views.approve_user, name='approve_user'),
]
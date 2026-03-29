from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (User, Property, PropertyImage, BookingRequest, 
                     Payment, MaintenanceRequest, Review, ContactMessage)


class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_approved', 'is_active']
    list_filter = ['user_type', 'is_approved', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'address', 'profile_picture', 'is_approved')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'address', 'is_approved')}),
    )


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'landlord', 'property_type', 'city', 'rent_amount', 'status', 'created_at']
    list_filter = ['property_type', 'status', 'city']
    search_fields = ['title', 'city', 'address']
    inlines = [PropertyImageInline]


class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'property', 'move_in_date', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['tenant__username', 'property__title']


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'payment_type', 'status', 'payment_date', 'transaction_id']
    list_filter = ['payment_type', 'status', 'payment_date']
    search_fields = ['transaction_id', 'booking__tenant__username']


class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'tenant', 'property', 'priority', 'status', 'created_at']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['title', 'tenant__username', 'property__title']


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'property', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['tenant__username', 'property__title']


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject']


admin.site.register(User, CustomUserAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(BookingRequest, BookingRequestAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(MaintenanceRequest, MaintenanceRequestAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
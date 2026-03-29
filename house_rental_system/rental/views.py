from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import User, Property, BookingRequest, Payment, MaintenanceRequest, Review, ContactMessage
from .forms import (UserRegistrationForm, PropertyForm, BookingRequestForm, 
                    PaymentForm, MaintenanceRequestForm, ReviewForm, ContactForm)
import uuid
from datetime import datetime, timedelta


def home(request):
    """Home page with featured properties and statistics"""
    featured_properties = Property.objects.filter(is_featured=True, status='available')[:6]
    total_properties = Property.objects.filter(status='available').count()
    total_landlords = User.objects.filter(user_type='landlord').count()
    total_tenants = User.objects.filter(user_type='tenant').count()
    
    context = {
        'featured_properties': featured_properties,
        'total_properties': total_properties,
        'total_landlords': total_landlords,
        'total_tenants': total_tenants,
    }
    return render(request, 'home.html', context)


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    """User login view with role-based redirection"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_approved:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect based on user type
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                elif user.user_type == 'landlord':
                    return redirect('landlord_dashboard')
                else:
                    return redirect('tenant_dashboard')
            else:
                messages.error(request, 'Your account is pending approval.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def password_reset(request):
    """Simple password reset page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            messages.success(request, 'Password reset link sent to your email!')
            # In production, you would send an actual email here
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email.')
    
    return render(request, 'password_reset.html')


def properties(request):
    """Property listing with search and filters"""
    property_list = Property.objects.filter(status='available')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        property_list = property_list.filter(
            Q(title__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Filter by property type
    property_type = request.GET.get('property_type', '')
    if property_type:
        property_list = property_list.filter(property_type=property_type)
    
    # Filter by city
    city = request.GET.get('city', '')
    if city:
        property_list = property_list.filter(city__icontains=city)
    
    # Filter by rent range
    min_rent = request.GET.get('min_rent', '')
    max_rent = request.GET.get('max_rent', '')
    if min_rent:
        property_list = property_list.filter(rent_amount__gte=min_rent)
    if max_rent:
        property_list = property_list.filter(rent_amount__lte=max_rent)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    property_list = property_list.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(property_list, 9)
    page_number = request.GET.get('page')
    properties_page = paginator.get_page(page_number)
    
    # Get unique cities for filter dropdown
    cities = Property.objects.values_list('city', flat=True).distinct()
    
    context = {
        'properties': properties_page,
        'cities': cities,
        'search_query': search_query,
        'property_type': property_type,
        'city': city,
        'min_rent': min_rent,
        'max_rent': max_rent,
        'sort_by': sort_by,
    }
    return render(request, 'properties.html', context)


def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    reviews = property_obj.reviews.all().order_by('-created_at')
    
    # Calculate average rating
    from django.db.models import Avg
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Split amenities into a list
    amenities_list = [amenity.strip() for amenity in property_obj.amenities.split(',') if amenity.strip()]
    
    context = {
        'property': property_obj,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'amenities_list': amenities_list,
    }
    return render(request, 'property_detail.html', context)


@login_required
def tenant_dashboard(request):
    """Tenant dashboard with bookings and payments"""
    if request.user.user_type != 'tenant':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    bookings = BookingRequest.objects.filter(tenant=request.user).order_by('-created_at')
    maintenance_requests = MaintenanceRequest.objects.filter(tenant=request.user).order_by('-created_at')
    
    # Get approved bookings for payment history
    approved_bookings = bookings.filter(status='approved')
    payments = Payment.objects.filter(booking__in=approved_bookings).order_by('-payment_date')
    
    # Statistics
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='pending').count()
    approved_bookings_count = bookings.filter(status='approved').count()
    total_paid = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'bookings': bookings,
        'maintenance_requests': maintenance_requests,
        'payments': payments,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings_count,
        'total_paid': total_paid,
    }
    return render(request, 'tenant_dashboard.html', context)


@login_required
def landlord_dashboard(request):
    """Landlord dashboard with properties and bookings"""
    if request.user.user_type != 'landlord':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    properties = Property.objects.filter(landlord=request.user).order_by('-created_at')
    booking_requests = BookingRequest.objects.filter(property__landlord=request.user).order_by('-created_at')
    maintenance_requests = MaintenanceRequest.objects.filter(property__landlord=request.user).order_by('-created_at')
    
    # Statistics
    total_properties = properties.count()
    available_properties = properties.filter(status='available').count()
    rented_properties = properties.filter(status='rented').count()
    pending_requests = booking_requests.filter(status='pending').count()
    
    # Revenue calculation
    approved_bookings = booking_requests.filter(status='approved')
    payments = Payment.objects.filter(booking__in=approved_bookings, status='completed')
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'properties': properties,
        'booking_requests': booking_requests,
        'maintenance_requests': maintenance_requests,
        'total_properties': total_properties,
        'available_properties': available_properties,
        'rented_properties': rented_properties,
        'pending_requests': pending_requests,
        'total_revenue': total_revenue,
    }
    return render(request, 'landlord_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard with all system data"""
    if not request.user.is_staff and request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    users = User.objects.all().order_by('-created_at')
    properties = Property.objects.all().order_by('-created_at')
    bookings = BookingRequest.objects.all().order_by('-created_at')
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    
    # Statistics
    total_users = users.count()
    total_tenants = users.filter(user_type='tenant').count()
    total_landlords = users.filter(user_type='landlord').count()
    total_properties = properties.count()
    total_bookings = bookings.count()
    pending_approvals = users.filter(is_approved=False).count()
    
    # Revenue
    total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'users': users[:10],
        'properties': properties[:10],
        'bookings': bookings[:10],
        'contact_messages': contact_messages[:10],
        'total_users': total_users,
        'total_tenants': total_tenants,
        'total_landlords': total_landlords,
        'total_properties': total_properties,
        'total_bookings': total_bookings,
        'pending_approvals': pending_approvals,
        'total_revenue': total_revenue,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def booking_request(request, property_id=None):
    """Create a new booking request"""
    if request.user.user_type != 'tenant':
        messages.error(request, 'Only tenants can make booking requests.')
        return redirect('properties')
    
    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tenant = request.user
            booking.save()
            messages.success(request, 'Booking request submitted successfully!')
            return redirect('tenant_dashboard')
    else:
        initial_data = {}
        if property_id:
            property_obj = get_object_or_404(Property, pk=property_id)
            initial_data['property'] = property_obj
        
        form = BookingRequestForm(initial=initial_data)
        # Filter to show only available properties
        form.fields['property'].queryset = Property.objects.filter(status='available')
    
    return render(request, 'booking_request.html', {'form': form})


@login_required
def approve_booking(request, booking_id):
    """Approve or reject a booking request"""
    if request.user.user_type != 'landlord':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    booking = get_object_or_404(BookingRequest, pk=booking_id, property__landlord=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            booking.status = 'approved'
            booking.property.status = 'rented'
            booking.property.save()
            messages.success(request, 'Booking approved successfully!')
        elif action == 'reject':
            booking.status = 'rejected'
            messages.success(request, 'Booking rejected.')
        
        booking.save()
    
    return redirect('landlord_dashboard')


@login_required
def payment(request, booking_id):
    """Process payment for a booking"""
    booking = get_object_or_404(BookingRequest, pk=booking_id)
    
    # Check if user is the tenant of this booking
    if request.user != booking.tenant:
        messages.error(request, 'Access denied.')
        return redirect('tenant_dashboard')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.transaction_id = str(uuid.uuid4())
            payment.status = 'completed'  # Dummy payment - auto complete
            payment.save()
            messages.success(request, 'Payment completed successfully!')
            return redirect('tenant_dashboard')
    else:
        # Pre-fill amount with rent amount
        initial_data = {
            'amount': booking.property.rent_amount,
            'payment_type': 'rent'
        }
        form = PaymentForm(initial=initial_data)
    
    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'payment.html', context)


@login_required
def add_property(request):
    """Add a new property (landlord only)"""
    if request.user.user_type != 'landlord':
        messages.error(request, 'Only landlords can add properties.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.landlord = request.user
            property_obj.save()
            messages.success(request, 'Property added successfully!')
            return redirect('landlord_dashboard')
    else:
        form = PropertyForm()
    
    return render(request, 'add_property.html', {'form': form})


@login_required
def edit_property(request, pk):
    """Edit an existing property"""
    property_obj = get_object_or_404(Property, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('landlord_dashboard')
    else:
        form = PropertyForm(instance=property_obj)
    
    return render(request, 'edit_property.html', {'form': form, 'property': property_obj})


@login_required
def delete_property(request, pk):
    """Delete a property"""
    property_obj = get_object_or_404(Property, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('landlord_dashboard')
    
    return render(request, 'delete_property.html', {'property': property_obj})


@login_required
def create_maintenance_request(request):
    """Create a maintenance request"""
    if request.user.user_type != 'tenant':
        messages.error(request, 'Only tenants can create maintenance requests.')
        return redirect('home')
    
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, request.FILES)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.tenant = request.user
            maintenance.save()
            messages.success(request, 'Maintenance request submitted successfully!')
            return redirect('tenant_dashboard')
    else:
        form = MaintenanceRequestForm()
        # Only show properties that the tenant has approved bookings for
        approved_bookings = BookingRequest.objects.filter(tenant=request.user, status='approved')
        property_ids = approved_bookings.values_list('property_id', flat=True)
        form.fields['property'].queryset = Property.objects.filter(id__in=property_ids)
    
    return render(request, 'create_maintenance.html', {'form': form})


@login_required
def update_maintenance_status(request, maintenance_id):
    """Update maintenance request status (landlord only)"""
    if request.user.user_type != 'landlord':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    maintenance = get_object_or_404(MaintenanceRequest, pk=maintenance_id, property__landlord=request.user)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'in_progress', 'completed']:
            maintenance.status = status
            maintenance.save()
            messages.success(request, f'Maintenance request status updated to {status}!')
    
    return redirect('landlord_dashboard')


@login_required
def add_review(request, property_id):
    """Add a review for a property"""
    property_obj = get_object_or_404(Property, pk=property_id)
    
    # Check if user has an approved booking for this property
    has_booking = BookingRequest.objects.filter(
        tenant=request.user, 
        property=property_obj, 
        status='approved'
    ).exists()
    
    if not has_booking:
        messages.error(request, 'You can only review properties you have rented.')
        return redirect('property_detail', pk=property_id)
    
    # Check if user already reviewed this property
    existing_review = Review.objects.filter(tenant=request.user, property=property_obj).first()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.tenant = request.user
            review.property = property_obj
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('property_detail', pk=property_id)
    else:
        form = ReviewForm(instance=existing_review)
    
    context = {
        'form': form,
        'property': property_obj,
        'is_edit': existing_review is not None,
    }
    return render(request, 'add_review.html', context)


def contact(request):
    """Contact form page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})


@login_required
def user_profile(request):
    """User profile page"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    
    return render(request, 'user_profile.html', {'user': request.user})


@login_required
def manage_users(request):
    """Admin page to manage users"""
    if not request.user.is_staff and request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    users = User.objects.all().order_by('-created_at')
    
    # Filter by user type
    user_type = request.GET.get('user_type', '')
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Filter by approval status
    approval_status = request.GET.get('approval_status', '')
    if approval_status == 'pending':
        users = users.filter(is_approved=False)
    elif approval_status == 'approved':
        users = users.filter(is_approved=True)
    
    # Pagination
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'user_type': user_type,
        'approval_status': approval_status,
    }
    return render(request, 'manage_users.html', context)


@login_required
@require_POST
def approve_user(request, user_id):
    """Approve a user account (admin only)"""
    if not request.user.is_staff and request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(User, pk=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f'User {user.username} has been approved!')
    
    return redirect('manage_users')


@login_required
@require_POST
def deactivate_user(request, user_id):
    """Deactivate a user account (admin only)"""
    if not request.user.is_staff and request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f'User {user.username} has been deactivated!')
    
    return redirect('manage_users')


@login_required
def manage_properties(request):
    """Admin page to manage all properties"""
    if not request.user.is_staff and request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    properties = Property.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        properties = properties.filter(status=status)
    
    # Filter by property type
    property_type = request.GET.get('property_type', '')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # Pagination
    paginator = Paginator(properties, 15)
    page_number = request.GET.get('page')
    properties_page = paginator.get_page(page_number)
    
    context = {
        'properties': properties_page,
        'status': status,
        'property_type': property_type,
    }
    return render(request, 'manage_properties.html', context)


@login_required
def payment_history(request):
    """View payment history"""
    if request.user.user_type == 'tenant':
        # Tenant sees their own payments
        bookings = BookingRequest.objects.filter(tenant=request.user, status='approved')
        payments = Payment.objects.filter(booking__in=bookings).order_by('-payment_date')
    elif request.user.user_type == 'landlord':
        # Landlord sees payments for their properties
        bookings = BookingRequest.objects.filter(property__landlord=request.user, status='approved')
        payments = Payment.objects.filter(booking__in=bookings).order_by('-payment_date')
    else:
        # Admin sees all payments
        payments = Payment.objects.all().order_by('-payment_date')
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    payments_page = paginator.get_page(page_number)
    
    # Calculate totals
    total_amount = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'payments': payments_page,
        'total_amount': total_amount,
    }
    return render(request, 'payment_history.html', context)


def about(request):
    """About page"""
    return render(request, 'about.html')


def terms(request):
    """Terms and conditions page"""
    return render(request, 'terms.html')


def privacy(request):
    """Privacy policy page"""
    return render(request, 'privacy.html')


# API Views for AJAX requests
@login_required
def get_property_details_ajax(request, property_id):
    """Get property details via AJAX"""
    property_obj = get_object_or_404(Property, pk=property_id)
    
    data = {
        'id': property_obj.id,
        'title': property_obj.title,
        'rent_amount': str(property_obj.rent_amount),
        'security_deposit': str(property_obj.security_deposit),
        'address': property_obj.address,
        'city': property_obj.city,
        'status': property_obj.status,
    }
    
    return JsonResponse(data)


@login_required
def search_properties_ajax(request):
    """Search properties via AJAX"""
    query = request.GET.get('q', '')
    
    properties = Property.objects.filter(
        Q(title__icontains=query) | 
        Q(city__icontains=query) | 
        Q(address__icontains=query),
        status='available'
    )[:10]
    
    results = [{
        'id': p.id,
        'title': p.title,
        'city': p.city,
        'rent_amount': str(p.rent_amount),
    } for p in properties]
    
    return JsonResponse({'results': results})
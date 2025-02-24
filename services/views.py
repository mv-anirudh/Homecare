from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from accounts.models import Certification,ServiceArea
from .models import Review, Service, ServiceCategory, Booking,AvailabilitySchedule
from .forms import BookingForm, ReviewForm, ServiceForm, ServiceSearchForm,AvailabilityForm
from datetime import *
from django.utils import timezone

class ServiceCreateView(CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'add_service.html'  
    success_url = reverse_lazy('service_list')  
    
    def form_valid(self, form):
        # Set the provider to the current user's ServiceProvider instance
        form.instance.provider = self.request.user.serviceprovider
        try:
            messages.success(self.request, "Service created successfully!")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating service: {str(e)}")
            return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a service provider
        if not hasattr(request.user, 'serviceprovider'):
            messages.error(request, "Only service providers can create services")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class ServiceListView(ListView):
    model = Service
    template_name = 'service_list.html'
    context_object_name = 'services'
    paginate_by = 12

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True).select_related(
            'provider', 'category'
        )
        
        form = ServiceSearchForm(self.request.GET)
        
        if form.is_valid():
            # Text search
            q = form.cleaned_data.get('q')
            if q:
                queryset = queryset.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q) |
                    Q(provider__business_name__icontains=q)
                )

            # Location search
            location = form.cleaned_data.get('location')
            if location:
                queryset = queryset.filter(
                    Q(provider__service_areas__city__icontains=location) |
                    Q(provider__service_areas__state__icontains=location) |
                    Q(provider__service_areas__zip_code__icontains=location)
                ).distinct()

            # Category filter
            category = form.cleaned_data.get('category')
            if category:
                queryset = queryset.filter(category=category)

            # Price range filter
            price_range = form.cleaned_data.get('price')
            if price_range:
                if price_range == '0-50':
                    queryset = queryset.filter(base_price__lte=50)
                elif price_range == '51-100':
                    queryset = queryset.filter(base_price__gt=50, base_price__lte=100)
                elif price_range == '101+':
                    queryset = queryset.filter(base_price__gt=100)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ServiceSearchForm(self.request.GET)
        context['categories'] = ServiceCategory.objects.all()
        
        # Preserve search parameters in pagination
        if self.request.GET:
            query_params = self.request.GET.copy()
            if 'page' in query_params:
                del query_params['page']
            context['query_params'] = query_params.urlencode()
        
        return context

class ServiceDetailView(DetailView):
    model = Service
    template_name = 'service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking_form'] = BookingForm(provider=self.object.provider)
        context['certifications'] = Certification.objects.filter(provider=self.object.provider)
        context['service_area'] = ServiceArea.objects.filter(provider=self.object.provider)
        context['availability_schedule'] = AvailabilitySchedule.objects.filter(provider=self.object.provider)
        context["review_form"] = ReviewForm()
        context["reviews"] = self.object.reviews.all().order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        return self.handle_review(request, service)

    def handle_review(self, request, service):
        form = ReviewForm(request.POST)
        if form.is_valid() and request.user.is_authenticated:
            # Check if the user has already reviewed this service
            existing_review = Review.objects.filter(service=service, user=request.user).first()
            
            if existing_review:
                # Update the existing review with new data
                existing_review.rating = form.cleaned_data['rating']
                existing_review.comment = form.cleaned_data['comment']
                existing_review.save()
                messages.success(request, "Your review has been updated!")
            else:
                review = form.save(commit=False)
                review.service = service
                review.user = request.user
                review.save()
                messages.success(request, "Thank you for your review!")
            
            return redirect('services:service_detail', pk=service.pk)
        
        messages.error(request, "Please correct the errors below.")
        return self.get(request)

class CreateBookingView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'create_booking.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, pk=self.kwargs['service_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('services:booking_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['provider'] = self.service.provider
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        context['provider'] = self.service.provider

        # Get available dates based on provider's schedule
        today = timezone.now().date()
        available_days = AvailabilitySchedule.objects.filter(
            provider=self.service.provider,
            is_available=True
        ).values_list('day_of_week', flat=True)

        valid_dates = [
            (today + timezone.timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(30)  # Allow booking up to 30 days in advance
            if (today + timezone.timedelta(days=i)).strftime('%A') in available_days
        ]

        context['available_dates'] = valid_dates
        return context

    def form_valid(self, form):
        try:
            form.instance.service = self.service
            form.instance.provider = self.service.provider
            form.instance.customer = self.request.user
            form.instance.total_amount = self.service.base_price
            form.instance.status = 'confirmed'
            response = super().form_valid(form)
            messages.success(self.request, 'Service booked successfully!')
            return response
        except Exception as e:
            messages.error(self.request, f'Booking failed: {str(e)}')
            return super().form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'booking_detail.html'
    context_object_name = 'booking'

    def test_func(self):
        booking = self.get_object()
        return (self.request.user == booking.customer or 
                self.request.user == booking.provider.user)

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.user_type == 'customer':
            return Booking.objects.filter(customer=self.request.user)
        return Booking.objects.filter(provider__user=self.request.user)


class AvailabilityView(LoginRequiredMixin, CreateView):
    model = AvailabilitySchedule
    form_class = AvailabilityForm
    template_name = "add_schedule.html"
    success_url = reverse_lazy('provider_dashboard')
    
    def get_queryset(self):
        # Restrict queryset to only show current provider's schedules
        return AvailabilitySchedule.objects.filter(provider=self.request.user.serviceprovider)
    
    def form_valid(self, form):
        # Set the provider to the current user's ServiceProvider instance
        form.instance.provider = self.request.user.serviceprovider
        try:
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, str(e))
            return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a service provider
        if not hasattr(request.user, 'serviceprovider'):
            messages.error(request, "Only service providers can manage schedules")
            return redirect('home')
            
        # Ensure providers can only access their own schedules
        if 'pk' in kwargs:
            schedule = self.get_queryset().filter(pk=kwargs['pk']).first()
            if schedule and schedule.provider != request.user.serviceprovider:
                raise PermissionDenied("You can only manage your own schedules")
                
        return super().dispatch(request, *args, **kwargs)



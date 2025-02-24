from datetime import datetime
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate,login,logout
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from accounts.models import ServiceProvider
from services.models import Booking, Service
from .forms import CertificationForm, ServiceAreaForm, ServiceProviderForm, UserRegistrationForm,SiginForm

# View for rendering the main index page
class IndexView(View):
    template_name="index.html"
    
    def get(self,request,*args,**kwargs):
        return render(request,self.template_name)

# View for handling user registration (sign up)
class SiginUpView(View):
    tempalte_name="Signup.html"
    form_class=UserRegistrationForm
    
    # Display the registration form
    def get (self,request,*args,**kwargs):
        form_instance=self.form_class
        return render(request,self.tempalte_name,{"form":form_instance})
    
    # Handle form submission for registration
    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)
        
        if form_instance.is_valid():    
            form_instance.save()
            return redirect("accounts:signin")
        return render(request,self.tempalte_name,{"form":form_instance})

# View for handling user login
class SigninView(View):
    template_name="Signin.html"
    form_class=SiginForm
    
    # Display the login form
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class
        return render(request,self.template_name,{"form":form_instance})
    
    # Handle login form submission
    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)
        
        if form_instance.is_valid():
            data=form_instance.cleaned_data
            uname=data.get("username")
            pwd=data.get("password")
            user_obj=authenticate(request,username=uname,password=pwd)
            
            if user_obj:
                login(request,user_obj)
                # Redirect to different pages based on user type
                if user_obj.user_type == 'service_provider':
                    return redirect("accounts:service_registration")
                elif user_obj.user_type == 'customer':
                    return redirect("accounts:customer_dashboard")
                return redirect("index")
        return render(request,self.template_name,{"form":form_instance})

# View for handling user logout
class SiginOut(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect("accounts:signin")   

# View for service provider registration with multiple forms
class ServiceProviderRegistrationView(LoginRequiredMixin, CreateView):
    model = ServiceProvider
    form_class = ServiceProviderForm
    template_name = 'service_provider_registration.html'
    success_url = reverse_lazy('accounts:provider_dashboard')

    # Check if user can access this view
    def dispatch(self, request, *args, **kwargs):
        # Prevent already registered providers from registering again
        if hasattr(request.user, 'serviceprovider'):
            return render(request, 'Service_Dashboard.html')
        
        # Only allow service provider type users    ``
        if not request.user.is_authenticated or request.user.user_type != 'service_provider':
            return render(request, 'customer_message.html')
        return super().dispatch(request, *args, **kwargs)

    # Add additional forms to context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['service_area_form'] = ServiceAreaForm(self.request.POST)
            context['certification_form'] = CertificationForm(self.request.POST)
        else:
            context['service_area_form'] = ServiceAreaForm(initial={'provider': None})
            context['certification_form'] = CertificationForm(initial={'provider': None})
        return context

    # Handle form submission and save all related data
    def form_valid(self, form):
        context = self.get_context_data()
        service_area_form = context['service_area_form']
        certification_form = context['certification_form']

        # Save all forms if valid using transaction
        if service_area_form.is_valid() and certification_form.is_valid():
            try:
                with transaction.atomic():
                    service_provider = form.save(commit=False)
                    service_provider.user = self.request.user
                    service_provider.save()

                    service_area = service_area_form.save(commit=False)
                    service_area.provider = service_provider
                    service_area.save()

                    certification = certification_form.save(commit=False)
                    certification.provider = service_provider
                    certification.save()

                return super().form_valid(form)
            except Exception as e:
                form.add_error(None, f"Registration failed: {str(e)}")
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

# Dashboard view for service providers
class ProviderDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Booking
    template_name = 'Service_Dashboard.html'
    context_object_name = 'recent_bookings'

    # Ensure only service providers can access this view
    def test_func(self):
        return self.request.user.user_type == 'service_provider'

    # Get recent bookings for the provider
    def get_queryset(self):
        return Booking.objects.filter(
            provider__user=self.request.user
        ).order_by('-created_at')[:5]

    # Add additional context data for the dashboard
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.request.user.serviceprovider
        today = datetime.now().date()

        # Add scheduling and booking information
        context.update({
            'days_of_week': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
            'morning_hours': ['6', '7', '8', '9', '10', '11', '12'],
            'afternoon_hours': ['13', '14', '15', '16', '17', '18', '19'],
            'pending_bookings': Booking.objects.filter(
                provider=provider,
                status='pending'
            ).count(),
            'today_bookings': Booking.objects.filter(
                provider=provider,
                booking_date=today
            ),
            'services': Service.objects.filter(provider=provider),
        })
        return context
    

class CustomerDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Booking
    template_name = 'customer_dashboard.html'
    context_object_name = 'customer_bookings'
    
    # Ensure only customers can access this view
    def test_func(self):
        return self.request.user.user_type == 'customer'
    
    # Get bookings for the customer
    def get_queryset(self):
        return Booking.objects.filter(
            customer=self.request.user
        ).order_by('-booking_date', '-booking_time')
    
    # Add additional context data for the dashboard
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.now().date()
        
        # Add relevant customer information
        context.update({
            'upcoming_bookings': Booking.objects.filter(
                customer=self.request.user,
                booking_date__gte=today,
                status='confirmed'
            ).order_by('booking_date', 'booking_time'),
            
            'pending_bookings': Booking.objects.filter(
                customer=self.request.user,
                status='pending'
            ).count(),
            
            'completed_bookings': Booking.objects.filter(
                customer=self.request.user,
                status='completed'
            ).count(),
            
        
            
            'favorite_providers': self.request.user.favorite_providers.all()[:3] if hasattr(self.request.user, 'favorite_providers') else [],
        })
        
        return context

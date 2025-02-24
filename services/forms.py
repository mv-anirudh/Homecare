from django import forms
from .models import AvailabilitySchedule, Review, Service, Booking, ServiceCategory
from django.core.exceptions import ValidationError
from datetime import *
from django.utils import timezone

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'name', 'description', 'base_price', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'base_price': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_base_price(self):
        price = self.cleaned_data.get('base_price')
        if price <= 0:
            raise ValidationError('Price must be greater than zero')
        return price

from django import forms
from django.utils import timezone
from .models import Booking, AvailabilitySchedule

class BookingForm(forms.ModelForm):
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Booking
        fields = ['booking_date', 'booking_time', 'special_instructions', 'service_location']
        widgets = {
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'special_instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'service_location': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)

        if self.provider:
            # Get available dates
            available_dates = AvailabilitySchedule.objects.filter(
                provider=self.provider,
                is_available=True
            ).values_list('day_of_week', flat=True)

            # Convert days of week to actual dates
            today = timezone.now().date()
            valid_dates = [
                today + timezone.timedelta(days=i)
                for i in range(30)  # Allow booking up to 30 days in advance
                if (today + timezone.timedelta(days=i)).strftime('%A') in available_dates
            ]

            self.fields['booking_date'].widget.attrs['min'] = valid_dates[0].strftime('%Y-%m-%d') if valid_dates else today.strftime('%Y-%m-%d')
            self.fields['booking_date'].widget.attrs['max'] = valid_dates[-1].strftime('%Y-%m-%d') if valid_dates else today.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        booking_time = cleaned_data.get('booking_time')

        if self.provider:
            # Validate the selected date
            day_of_week = booking_date.strftime('%A')
            availability = AvailabilitySchedule.objects.filter(
                provider=self.provider,
                day_of_week=day_of_week,
                is_available=True
            ).first()

            if not availability:
                raise forms.ValidationError('The selected date is not available for booking.')

            # Validate the selected time
            if booking_time and (booking_time < availability.start_time or booking_time > availability.end_time):
                raise forms.ValidationError('Selected time is outside provider availability.')

        return cleaned_data


# forms.py


class ServiceSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
               'placeholder': 'What service do you need?'}
    ))
    location = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
               'placeholder': 'Location'}
    ))
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'px-4 py-2 rounded-lg border border-gray-300'})
    )
    price = forms.ChoiceField(
        choices=[
            ('', 'Price Range'),
            ('0-50', '$0 - $50'),
            ('51-100', '$51 - $100'),
            ('101+', '$101+')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'px-4 py-2 rounded-lg border border-gray-300'})
    )
    
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': '0', 'max': '5', 'step': '0.1'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review...'}),
        }
        
class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySchedule
        # Exclude provider field to prevent providers from seeing/selecting other providers
        exclude = ['provider']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
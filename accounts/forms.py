from django import forms
from accounts.models import Certification, User,ServiceProvider,ServiceArea
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

# Form for registering new users
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        # List of fields that will be shown in the registration form
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 
                  'last_name', 'user_type', 'phone_number', 'address', 'city', 
                  'state', 'zip_code', 'profile_picture', 'bio', 'preferred_communication']

# Form for service providers to enter their business details
class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ['business_name', 'description', 'experience_years']
        # Adding form-control class to make form fields look better
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove automatic fields that should not be filled by users
        self.fields.pop('is_verified', None)
        self.fields.pop('rating', None)
        self.fields.pop('total_reviews', None)
        self.fields.pop('status', None)

# Form for service providers to specify their service areas
class ServiceAreaForm(forms.ModelForm):
    class Meta:
        model = ServiceArea
        fields = ['city', 'state', 'zip_code']
        # Adding Bootstrap styling to form fields
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove provider field as it will be set automatically in the view
        self.fields.pop('provider', None)

# Form for service providers to add their certifications
class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'issued_by', 'issued_date', 'expiry_date', 'document_url']
        # Adding Bootstrap styling and setting date input type for date fields
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'issued_by': forms.TextInput(attrs={'class': 'form-control'}),
            'issued_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'document_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove provider field as it will be set automatically in the view
        self.fields.pop('provider', None)

# Form for user login
class SiginForm(forms.Form):
        username=forms.CharField(widget=forms.TextInput(attrs={"class":"form-control"}))
        password=forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control"}))
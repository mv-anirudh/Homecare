from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    user_type = models.CharField(max_length=20, choices=[
        ('customer', 'Customer'),
        ('service_provider', 'Service Provider')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    preferred_communication = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('both', 'Both')
        ],
        default='email'
    )
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('suspended', 'Suspended')
        ],
        default='active'
    )

    def __str__(self):
        return self.email

class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)
    description = models.TextField()
    experience_years = models.IntegerField()
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)]
    )
    total_reviews = models.IntegerField(default=0)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.business_name



class ServiceArea(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='service_areas')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.city}, {self.state} - {self.zip_code}"

class Certification(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255)
    issued_by = models.CharField(max_length=255)
    issued_date = models.DateField()
    expiry_date = models.DateField()
    document_url = models.URLField()

    def __str__(self):
        return f"{self.name} - {self.provider.business_name}"



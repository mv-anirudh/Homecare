from django.contrib import admin

# Register your models here.
from services.models import ServiceCategory,Service,ServiceImage,ServiceProvider,AvailabilitySchedule,Booking

admin.site.register(Service)
admin.site.register(ServiceCategory)
admin.site.register(ServiceImage)
admin.site.register(AvailabilitySchedule)
admin.site.register(Booking)
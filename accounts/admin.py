from django.contrib import admin
from .models import ServiceProvider,User,ServiceArea,Certification

# Register your models here.
admin.site.register(ServiceArea)
admin.site.register(User)
admin.site.register(ServiceProvider)
admin.site.register(Certification)
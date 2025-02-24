from django.urls import path
from accounts import views

app_name = "accounts" 
urlpatterns = [
    path("signup/",views.SiginUpView.as_view(),name="signup"),
    path("signin/",views.SigninView.as_view(),name="signin"),
    path("signout/",views.SiginOut.as_view(),name="signout"),
    path("service/registration/",views.ServiceProviderRegistrationView.as_view(),name="service_registration"),
    path('dashboard/', views.ProviderDashboardView.as_view(), name='provider_dashboard'),
    path('customer/dashboard/',views.CustomerDashboardView.as_view(), name='customer_dashboard'),
   
]

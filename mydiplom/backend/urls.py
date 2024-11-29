

from django.urls import path

from backend.views import UserRegistration

urlpatterns = [
    # path('login', ),
    path('register', UserRegistration.as_view(), name='user-register'),
    
]
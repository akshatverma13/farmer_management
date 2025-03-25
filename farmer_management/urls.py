"""
URL configuration for farmer_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter #
from farmers.views import FarmerViewSet, LoginAPIView, UserCreateAPIView

router = DefaultRouter()
router.register(r'farmers', FarmerViewSet)
urlpatterns = [
    path('', include('farmers.urls')),
    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('api/users/', UserCreateAPIView.as_view(), name='user-create'),
    path('api/', include(router.urls)),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
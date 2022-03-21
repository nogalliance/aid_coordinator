"""aid_coordinator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.contrib import admin
from django.contrib.auth.views import PasswordResetView
from django.urls import path, include
from rest_framework import routers

from contacts.api import OrganisationViewSet, ContactViewSet
from supply_demand.api import OfferItemViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'personal_donors', ContactViewSet)
router.register(r'donor_organisations', OrganisationViewSet)
router.register(r'offered_items', OfferItemViewSet)

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path("admin/password_reset/", PasswordResetView.as_view(), name="admin_password_reset"),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('__debug__/', include('debug_toolbar.urls')),
]

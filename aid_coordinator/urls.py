from django.contrib import admin
from django.contrib.auth.views import PasswordResetView
from django.urls import path, include
from rest_framework import routers

from contacts.api import DonorOrganisationViewSet, PersonalDonorViewSet
from supply_demand.api import OfferItemViewSet, RequestItemViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'personal_donors', PersonalDonorViewSet)
router.register(r'donor_organisations', DonorOrganisationViewSet)
router.register(r'offered_items', OfferItemViewSet)
router.register(r'requested_items', RequestItemViewSet)

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path("admin/password_reset/", PasswordResetView.as_view(), name="admin_password_reset"),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('__debug__/', include('debug_toolbar.urls')),
]

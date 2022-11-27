from django.contrib import admin
from django.contrib.auth.views import PasswordResetView
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from django_registration.backends.activation.views import RegistrationView
from rest_framework import routers

from aid_coordinator.views import ClaimAutocompleteView
from contacts.api import DonorOrganisationViewSet, PersonalDonorViewSet
from contacts.forms import ContactRegistrationForm
from logistics.views import RequestView, OfferView
from supply_demand.api import OfferItemViewSet, RequestItemViewSet

# Change titles
admin.site.site_title = _("Keep Ukraine Connected")
admin.site.site_header = _("GNA Keep Ukraine Connected back-end")
admin.site.index_title = _("Donation administration")

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r"personal_donors", PersonalDonorViewSet)
router.register(r"donor_organisations", DonorOrganisationViewSet)
router.register(r"offered_items", OfferItemViewSet)
router.register(r"requested_items", RequestItemViewSet)

urlpatterns = [
    path(
        "accounts/register/",
        RegistrationView.as_view(form_class=ContactRegistrationForm),
        name="django_registration_register",
    ),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/request/<int:item_id>/", RequestView.as_view(), name="request"),
    path("admin/offer/<int:item_id>/", OfferView.as_view(), name="offer"),
    path(
        "admin/autocomplete/claim/",
        ClaimAutocompleteView.as_view(admin_site=admin.site),
        name="autocomplete_claim",
    ),
    path(
        "admin/password_reset/",
        PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("__debug__/", include("debug_toolbar.urls")),
    path('', RedirectView.as_view(url='/admin/'), name='go-to-admin'),
]

from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.views.generic import FormView

from supply_demand.models import OfferItem


class ClaimAutocompleteView(AutocompleteJsonView):
    def serialize_result(self, obj, to_field_name):
        """
        Convert the provided model object to a dictionary that is added to the
        results list.
        """
        if isinstance(obj, OfferItem):
            if obj.amount:
                amount = f"{obj.amount - obj.claimed}x"
            else:
                amount = "Multiple"

            if obj.offer.contact.organisation_id:
                donor = obj.offer.contact.organisation
            else:
                donor = obj.offer.contact

            return {
                "id": str(getattr(obj, to_field_name)),
                "text": f"{amount} {obj} {obj.notes} [{donor}]"
            }
        else:
            return super().serialize_result(obj, to_field_name)


class AdminFormView(FormView):
    admin_model = None

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.setdefault('request', self.request)
        data.setdefault("site_title", admin.site.site_title)
        data.setdefault("site_header", admin.site.site_header)
        data.setdefault("has_permission", admin.site.has_permission(self.request))

        # noinspection PyProtectedMember
        data.setdefault('opts', self.admin_model._meta)

        return data

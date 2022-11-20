from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from aid_coordinator.views import AdminFormView
from logistics.forms import RequestForm
from supply_demand.models import Claim, OfferItem, Request, RequestItem, Offer


class RequestView(AdminFormView):
    template_name = "admin/request.html"
    form_class = RequestForm
    admin_model = OfferItem

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = None

    def get(self, request, *args, **kwargs):
        self.item = get_object_or_404(OfferItem, pk=kwargs.pop("item_id"))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.item = get_object_or_404(OfferItem, pk=kwargs.pop("item_id"))
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["item"] = self.item
        return data

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["amount"] = forms.IntegerField(
            label=_('How many of "{item}{notes}" would you like?').format(
                item=self.item, notes=f" ({self.item.notes})" if self.item.notes else ""
            ),
            initial=1,
            min_value=1,
            max_value=self.item.available,
        )
        return form

    def form_valid(self, form):
        today = timezone.now()
        amount = form.cleaned_data["amount"]
        request, new = Request.objects.get_or_create(contact=self.request.user, goal=f"Requests of {today:%Y-%m-%d}")
        item = RequestItem.objects.create(
            request=request,
            type=self.item.type,
            brand=self.item.brand,
            model=self.item.model,
            notes=self.item.notes,
            amount=amount,
        )

        Claim.objects.create(offered_item=self.item, requested_item=item, amount=amount)
        messages.info(
            self.request,
            _("Request for {amount}x {item} created").format(
                amount=amount,
                item=self.item,
            ),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin:supply_demand_offeritem_changelist")


class OfferView(AdminFormView):
    template_name = "admin/offer.html"
    item = None
    form_class = RequestForm
    admin_model = RequestItem

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(RequestItem, pk=kwargs.pop("item_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["item"] = self.item
        return data

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["amount"] = forms.IntegerField(
            label=_('How many of "{item}{notes}" would you like to donate({needed} max)?').format(
                item=self.item,
                notes=f" ({self.item.notes})" if self.item.notes else "",
                needed=self.item.needed,
            ),
            initial=self.item.needed,
            min_value=1,
            max_value=self.item.needed,
        )
        return form

    def form_valid(self, form):
        today = timezone.now()
        amount = form.cleaned_data["amount"]
        offer, new = Offer.objects.get_or_create(contact=self.request.user, description=f"Offer of {today:%Y-%m-%d}")
        item = OfferItem.objects.create(
            offer=offer,
            type=self.item.type,
            brand=self.item.brand,
            model=self.item.model,
            notes=self.item.notes,
            amount=amount,
        )

        Claim.objects.create(offered_item=item, requested_item=self.item, amount=amount)
        messages.info(
            self.request,
            _("Offer for {amount}x {item} created").format(
                amount=amount,
                item=self.item,
            ),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin:supply_demand_requestitem_changelist")

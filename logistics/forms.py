from django import forms
from django.utils.translation import gettext_lazy as _

from logistics.models import ShipmentItem, Shipment, ShipmentStatus


class AssignToShipmentForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ("shipment",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shipment_queryset = kwargs.get("initial", {}).get("shipment_queryset", None)
        if shipment_queryset is None:
            shipment_queryset = Shipment.objects.filter()
        shipments = shipment_queryset.filter(status=ShipmentStatus.PENDING)
        choices = [(shipment.id, shipment.name) for shipment in shipments]
        choices.insert(0, ("new", _("New shipment")))
        self.fields["shipment"].choices = choices


class RequestForm(forms.Form):
    pass

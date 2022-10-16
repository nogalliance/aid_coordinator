from django import forms

from logistics.models import ShipmentItem, Shipment


class AssignToShipmentForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ("shipment",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shipment_queryset = kwargs.get("initial", {}).get("shipment_queryset", None)
        if shipment_queryset is None:
            shipment_queryset = Shipment.objects.filter()
        shipment_choices = shipment_queryset.filter(is_delivered=False).values_list("id", "name")
        self.fields["shipment"].choices = shipment_choices


class RequestForm(forms.Form):
    pass

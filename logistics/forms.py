from django import forms

from logistics.models import ShipmentItem, Shipment


class AssignToShipmentForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ("shipment",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["shipment"].choices = Shipment.objects.exclude(is_delivered=True).values_list("id", "name")


class RequestForm(forms.Form):
    pass

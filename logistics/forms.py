from django import forms

from logistics.models import ShipmentItem


class AssignToShipmentForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ("shipment",)


class RequestForm(forms.Form):
    pass

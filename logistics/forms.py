from django import forms

from logistics.models import Claim


class AssignToShipmentForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ('shipment',)


class RequestForm(forms.Form):
    pass

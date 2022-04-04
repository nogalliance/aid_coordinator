from django import forms

from supply_demand.models import OfferItem, RequestItem


class MoveToOfferForm(forms.ModelForm):
    class Meta:
        model = OfferItem
        fields = ('offer',)


class MoveToRequestForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ('request',)

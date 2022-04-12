from django import forms

from supply_demand.models import Offer, OfferItem, RequestItem


class MoveToOfferForm(forms.ModelForm):
    offer = forms.ModelChoiceField(
        queryset=Offer.objects.order_by('contact__organisation', 'contact__last_name', 'contact__first_name',
                                        'description')
    )

    class Meta:
        model = OfferItem
        fields = ('offer',)


class MoveToRequestForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ('request',)

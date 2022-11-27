from django import forms

from supply_demand.models import ItemType, Offer, OfferItem, RequestItem


class MoveToOfferForm(forms.ModelForm):
    offer = forms.ModelChoiceField(
        queryset=Offer.objects.order_by(
            "contact__organisation",
            "contact__last_name",
            "contact__first_name",
            "description",
        )
    )

    class Meta:
        model = OfferItem
        fields = ("offer",)


class MoveToRequestForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ("request",)


def change_type_form_factory(old_class):
    """
    Returns an ActionForm subclass containing a ChoiceField populated with
    the given types.
    """
    class _NewTypeActionForm(old_class):
        """
        Action form with new type ChoiceField.
        """
        new_type = forms.ModelChoiceField(ItemType.objects.all(), required=False)
    _NewTypeActionForm.__name__ = str('NewTypeActionForm')

    return _NewTypeActionForm

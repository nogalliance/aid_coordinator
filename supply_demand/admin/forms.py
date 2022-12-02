from django import forms
from django.forms.models import BaseInlineFormSet

from supply_demand.models import ItemType, Offer, OfferItem, RequestItem


class RequestItemInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        instance = form.instance
        if hasattr(instance, "processed") and not instance.processed:
            form.fields["DELETE"].disabled = True
        else:
            form.fields["DELETE"].disabled = False


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

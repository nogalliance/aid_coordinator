from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _

from contacts.models import Contact


class ContactForm(UserChangeForm):
    send_welcome_email = forms.BooleanField(label=_('Send welcome email'), initial=False, required=False)

    class Meta:
        model = Contact
        fields = '__all__'


class AddContactForm(forms.ModelForm):
    send_welcome_email = forms.BooleanField(label=_('Send welcome email'), initial=True, required=False)

    class Meta:
        model = Contact
        fields = '__all__'

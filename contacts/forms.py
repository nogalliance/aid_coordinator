from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _

from contacts.models import Contact

email_text = """Hello {{ contact.first_name }},

{% if contact.is_donor -%}
You have been registered as a donor to the Keep Ukraine Connected task force
of the Global NOG Alliance.
{%- elif contact.is_requester -%}
You have been registered as an organisation from Ukraine that would like to
receive support from the Keep Ukraine Connected task force of the Global NOG
Alliance.
{%- endif %}
{%- if contact.organisation %}

You have been registered as a contact for {{ contact.organisation }}.
{%- endif %}

…
…
…

Yours,


Everyone at Keep Ukraine Connected

A task force from the Global NOG Alliance
https://www.nogalliance.org
"""


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


class EmailForm(forms.Form):
    sender = forms.EmailField(widget=forms.TextInput(attrs={'size': '40'}), initial='ukraine@nogalliance.org')
    subject = forms.CharField(widget=forms.TextInput(attrs={'size': '76'}),
                              initial='Notification from KeepUkraineConnected')
    content = forms.CharField(
        widget=forms.Textarea(attrs={"cols": "76", "rows": "30", "style": "font-family: monospace"}),
        initial=email_text)

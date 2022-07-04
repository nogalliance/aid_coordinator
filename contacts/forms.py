from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group
from django.core.mail import mail_admins
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm, RegistrationFormCaseInsensitive

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
{%- elif contact.requested_organisation %}

You have requested to be registered as a contact for
{{ contact.requested_organisation }}.
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


class ContactRegistrationForm(RegistrationFormCaseInsensitive):
    account_type = forms.ChoiceField(
        label=_('Account type'), choices=(
            ('donor', _('Donor')),
            ('requester', _('Requester')),
        ),
        widget=forms.RadioSelect
    )
    requested_organisation = forms.CharField(
        label=_('Organisation'),
        widget=forms.TextInput,
        help_text=_('Please indicate the organisation you represent'),
    )
    description = forms.CharField(
        label=_('Description'),
        widget=forms.Textarea,
        help_text=_('Please describe why you create this account')
    )

    class Meta(RegistrationForm.Meta):
        model = Contact
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'requested_organisation',
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        account_type = self.cleaned_data.get('account_type')
        if account_type == 'donor':
            group = Group.objects.get(name='Donors')
        elif account_type == 'requester':
            group = Group.objects.get(name='Requesters')
        else:
            group = None

        user = super().save(commit=commit)
        if group:
            user.groups.add(group)

        # Notify admins
        mail_admins(
            subject=f"New {account_type} user self-registered: {user.username}",
            message=f"Self-registration details\n"
                    f"=========================\n"
                    f"Username:      {user.username}\n"
                    f"First name:    {user.first_name}\n"
                    f"Last name:     {user.last_name}\n"
                    f"Email address: {user.email}\n"
                    f"Organisation:  {user.requested_organisation}\n"
                    f"\n"
                    f"Account type:  {account_type}\n"
                    f"Description:\n"
                    f"{self.cleaned_data.get('description')}",
            fail_silently=True,
        )

        return user

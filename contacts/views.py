from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template import Template
from django.utils.decorators import method_decorator
from django.utils.translation import ngettext
from jinja2 import Template

from aid_coordinator.decorators import superuser_required
from aid_coordinator.views import AdminFormView
from contacts.forms import EmailForm
from contacts.models import Contact


@method_decorator(superuser_required(), name='dispatch')
class EmailView(AdminFormView):
    template_name = 'admin/email.html'
    form_class = EmailForm
    admin_model = Contact

    def form_valid(self, form: EmailForm):
        count = 0
        for contact in Contact.objects.filter(pk__in=self.request.GET['contacts'].split(',')):
            context = {
                'contact': contact
            }
            text = Template(form.cleaned_data['content']).render(context)
            contact.email_user(
                from_email=form.cleaned_data['sender'],
                subject=form.cleaned_data['subject'],
                message=text,
            )
            count += 1

        messages.add_message(request=self.request, level=messages.INFO, message=ngettext(
            "%(count)s message has been sent",
            "%(count)s messages have been sent",
            count
        ) % {'count': count})

        return HttpResponseRedirect('..')

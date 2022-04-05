from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template import Template
from django.utils.decorators import method_decorator
from django.utils.translation import ngettext
from django.views.generic import FormView
from jinja2 import Template

from aid_coordinator.decorators import superuser_required
from contacts.forms import EmailForm
from contacts.models import Contact


@method_decorator(superuser_required(), name='dispatch')
class EmailView(FormView):
    template_name = 'admin/email.html'
    form_class = EmailForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.setdefault('request', self.request)
        data.setdefault('opts', Contact._meta)
        data.setdefault("site_title", admin.site.site_title)
        data.setdefault("site_header", admin.site.site_header)
        data.setdefault("has_permission", admin.site.has_permission(self.request))
        return data

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

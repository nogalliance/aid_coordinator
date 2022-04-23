from django.contrib import admin
from django.views.generic import FormView


class AdminFormView(FormView):
    admin_model = None

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.setdefault('request', self.request)
        data.setdefault("site_title", admin.site.site_title)
        data.setdefault("site_header", admin.site.site_header)
        data.setdefault("has_permission", admin.site.has_permission(self.request))

        # noinspection PyProtectedMember
        data.setdefault('opts', self.admin_model._meta)

        return data

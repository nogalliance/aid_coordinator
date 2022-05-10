from django.contrib import admin
from django.db.models import F, QuerySet
from django.utils.translation import gettext_lazy as _


class OverclaimedListFilter(admin.SimpleListFilter):
    title = _('overclaimed')
    parameter_name = 'overclaimed'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset: QuerySet):
        if self.value() == 'yes':
            return queryset.filter(claimed__gt=F('amount'))
        if self.value() == 'yes':
            return queryset.filter(claimed__lte=F('amount'))
        else:
            return queryset

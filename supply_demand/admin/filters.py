from django.contrib import admin
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


class ClaimedFilter(admin.SimpleListFilter):
    title = _('claimed')
    parameter_name = 'is_claimed'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset: QuerySet):
        if self.value() == 'yes':
            return queryset.exclude(claimed_by=None)
        elif self.value() == 'no':
            return queryset.filter(claimed_by=None)
        else:
            return queryset

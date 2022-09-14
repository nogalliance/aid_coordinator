from django.contrib.admin import SimpleListFilter
from django.db.models import F, Q, QuerySet
from django.utils.translation import gettext_lazy as _


class RequestedOrganisationFilter(SimpleListFilter):
    title = _("requested organisation")
    parameter_name = "req_org"

    def lookups(self, request, model_admin):
        return (
            ("none", _("None")),
            ("diff", _("Different")),
            ("same", _("Correct")),
        )

    def queryset(self, request, queryset: QuerySet):
        option = self.value()

        if option == "none":
            return queryset.filter(requested_organisation="", organisation=None)
        elif option == "diff":
            return queryset.filter(
                ~Q(requested_organisation="")
                & (Q(organisation__isnull=True) | ~Q(requested_organisation=F("organisation__name")))
            )
        elif option == "same":
            return queryset.filter(
                Q(requested_organisation="", organisation__isnull=False)
                | Q(requested_organisation=F("organisation__name"))
            )
        else:
            return queryset

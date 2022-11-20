from django.db.models import Subquery


class SubquerySum(Subquery):
    # https://code.djangoproject.com/ticket/10060
    template = "(SELECT sum(_sum.%(column)s) FROM (%(subquery)s) _sum)"

    def __init__(self, queryset, column, output_field=None, **extra):
        if output_field is None:
            output_field = queryset.model._meta.get_field(column)
        super().__init__(queryset, output_field, column=column, **extra)

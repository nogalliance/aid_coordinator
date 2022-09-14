from urllib.parse import parse_qs

from django.contrib import admin


class UsedChoicesFieldListFilter(admin.ChoicesFieldListFilter):
    def choices(self, changelist):
        used_values = set(self.field.model.objects.all().values_list(self.field.attname, flat=True).distinct())
        for option in super().choices(changelist):
            query = parse_qs(option["query_string"].lstrip("?"))
            if self.lookup_kwarg in query:
                if used_values.intersection(query[self.lookup_kwarg]):
                    yield option
            else:
                yield option

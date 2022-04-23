from django.contrib.admin.widgets import AutocompleteSelect
from django.urls import reverse


class ClaimAutocompleteSelect(AutocompleteSelect):
    def get_url(self):
        return reverse('autocomplete_claim')

from django.contrib import admin
from django.forms import NumberInput, TextInput


class CompactInline(admin.TabularInline):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)

        if db_field.name == 'brand':
            field.widget = TextInput(attrs={'style': 'width: 5em', 'maxlength': 50})
        elif db_field.name == 'model':
            field.widget = TextInput(attrs={'style': 'width: 16em', 'maxlength': 50})
        elif db_field.name == 'notes':
            field.widget = TextInput(attrs={'style': 'width: 16em', 'maxlength': 250})
        elif db_field.name in ['amount', 'up_to']:
            field.widget = NumberInput(attrs={'style': 'width: 3em', 'min': 0, 'max': 999})

        return field

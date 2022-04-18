from django.conf import settings as django_settings


# noinspection PyUnusedLocal
def settings(request):
    """
    Add registration_open variable to the context.
    """
    return {"SETTINGS": django_settings}

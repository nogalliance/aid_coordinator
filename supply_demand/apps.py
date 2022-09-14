from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SupplyDemandConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "supply_demand"
    verbose_name = _("Supply & Demand")

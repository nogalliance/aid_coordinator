from django.db import models
from django.utils import timezone

from supply_demand.models import OfferItem, RequestItem

from django.utils.translation import gettext_lazy as _


class Shipment(models.Model):
    name = models.CharField(verbose_name=_('name'), max_length=100, unique=True)
    when = models.DateField(verbose_name=_('when'), blank=True, null=True)
    is_delivered = models.BooleanField(verbose_name=_('is delivered'), default=False)

    class Meta:
        verbose_name = _('shipment')
        verbose_name_plural = _('shipments')

    def __str__(self):
        return self.name


class Claim(models.Model):
    offered_item = models.ForeignKey(verbose_name=_('offered item'), to=OfferItem, on_delete=models.RESTRICT)
    requested_item = models.ForeignKey(verbose_name=_('requested item'), to=RequestItem, on_delete=models.RESTRICT)
    amount = models.PositiveIntegerField(verbose_name=_('amount'), default=1,
                                         help_text=_('The amount of items claimed'))
    when = models.DateField(verbose_name=_('when'), default=timezone.now)
    shipment = models.ForeignKey(verbose_name=_('shipment'), to=Shipment, blank=True, null=True,
                                 on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _('claim')
        verbose_name_plural = _('claims')

    def __str__(self):
        return f"{self.amount}x {self.offered_item} for request {self.requested_item}"

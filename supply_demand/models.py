from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from contacts.models import Organisation, Contact


class ItemType(models.IntegerChoices):
    OTHER = 0, _('Other')
    HARDWARE = 100, _('Hardware')
    SOFTWARE = 200, _('Software')
    SERVICE = 300, _('Service')


class DeliveryMethod(models.IntegerChoices):
    UNKNOWN = 0, _('Unknown')
    SEND_TO_GNA = 100, _('Send to GNA by donor')
    PICKUP_REQUESTED = 200, _('Pickup requested')
    OTHER = 999, _('Other')


class Request(models.Model):
    contact = models.ForeignKey(verbose_name=_('contact'), to=Contact, related_name='requests',
                                on_delete=models.RESTRICT)

    goal = models.CharField(verbose_name=_('goal'), max_length=100,
                            help_text=_('Give a short description of what this request is for'))
    description = models.TextField(verbose_name=_('description'),
                                   help_text=_('Provide more detail on this request, this is your elevator pitch!'))
    internal_notes = models.TextField(verbose_name=_('internal notes'), blank=True,
                                      help_text=_('Internal notes that will NOT be shown publicly'))

    class Meta:
        ordering = ('contact__organisation__name', 'contact__last_name', 'contact__first_name', 'goal')
        verbose_name = _('request')
        verbose_name_plural = _('requests')

    def __str__(self):
        return self.goal


class RequestItem(models.Model):
    request = models.ForeignKey(verbose_name=_('request'), to=Request, related_name='items', on_delete=models.RESTRICT)
    type = models.PositiveIntegerField(verbose_name=_('type'), choices=ItemType.choices, default=ItemType.OTHER)
    brand = models.CharField(verbose_name=_('brand'), max_length=50, blank=True,
                             help_text=_('Either a brand name or a description of the kind of brand'))
    model = models.CharField(verbose_name=_('model'), max_length=50, blank=True,
                             help_text=_('Either an explicit model or a description of the required features'))
    amount = models.PositiveIntegerField(verbose_name=_('# required'), default=1,
                                         help_text=_('The minimal amount that you need'))
    up_to = models.PositiveIntegerField(verbose_name=_('up to'), blank=True, null=True,
                                        help_text=_('The maximum amount that you could use'))

    notes = models.CharField(verbose_name=_('notes'), max_length=250, blank=True,
                             help_text=_('Any extra information that can help a donor decide if they have something '
                                         'that can help you'))
    alternative_for = models.ForeignKey(verbose_name=_('alternative for'), to='RequestItem', blank=True, null=True,
                                        related_name='alternatives', on_delete=models.CASCADE,
                                        help_text=_('In case there are multiple options to solve your problem'))

    class Meta:
        ordering = ('type', 'brand', 'model')
        verbose_name = _('request item')
        verbose_name_plural = _('request items')

    def __str__(self):
        return f"{self.amount}x {self.brand} {self.model}"

    def clean(self):
        super().clean()

        if self.alternative_for_id and self.id:
            if self.alternative_for_id == self.id:
                raise ValidationError({'alternative_for': "An item can't be an alternative for itself"})

            alt = self.alternative_for
            while alt:
                if alt.id == self.id:
                    raise ValidationError({'alternative_for': "Alternatives can't form a loop"})
                alt = alt.alternative_for if alt.alternative_for_id else None


class Offer(models.Model):
    contact = models.ForeignKey(verbose_name=_('contact'), to=Contact, related_name='offers', on_delete=models.RESTRICT)
    description = models.CharField(verbose_name=_('description'), max_length=100,
                                   help_text=_('Give a short description of what this offer is'))
    location = models.TextField(verbose_name=_('location'), blank=True,
                                help_text=_('Where is the equipment coming from?'))
    delivery_method = models.IntegerField(verbose_name=_('delivery method'), choices=DeliveryMethod.choices,
                                          default=DeliveryMethod.UNKNOWN)
    internal_notes = models.TextField(verbose_name=_('internal notes'), blank=True,
                                      help_text=_('Internal notes that will NOT be shown publicly'))

    class Meta:
        ordering = ('description', 'contact__organisation__name', 'contact__first_name', 'contact__last_name')
        verbose_name = _('offer')
        verbose_name_plural = _('offers')

    def __str__(self):
        if self.contact.organisation_id:
            return f"{self.contact.organisation}: {self.description}"
        else:
            return f"{self.contact}: {self.description}"


class OfferItem(models.Model):
    offer = models.ForeignKey(verbose_name=_('offer'), to=Offer, related_name='items', on_delete=models.RESTRICT)
    type = models.PositiveIntegerField(verbose_name=_('type'), choices=ItemType.choices, default=ItemType.OTHER)
    brand = models.CharField(verbose_name=_('brand'), max_length=50, blank=True)
    model = models.CharField(verbose_name=_('model'), max_length=50)
    amount = models.PositiveIntegerField(verbose_name=_('# offered'), null=True, blank=True)
    notes = models.CharField(verbose_name=_('notes'), max_length=250, blank=True,
                             help_text=_('Any extra information that can help a donor decide if they have something '
                                         'that can help you'))

    received = models.BooleanField(verbose_name=_('received'), default=False)
    claimed_by = models.ForeignKey(verbose_name=_('claimed by'), to=Contact, blank=True, null=True,
                                   related_name='claimed_items', on_delete=models.SET_NULL)

    class Meta:
        ordering = ('type', 'brand', 'model')
        verbose_name = _('offer item')
        verbose_name_plural = _('offer items')

    def __str__(self):
        if self.amount:
            return f"{self.amount}x {self.brand} {self.model}"

        return f"Multiple {self.brand} {self.model}"

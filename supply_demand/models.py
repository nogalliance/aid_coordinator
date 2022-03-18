from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from contacts.models import Organisation, Contact


class Request(models.Model):
    organisation = models.ForeignKey(verbose_name=_('organisation'), to=Organisation, on_delete=models.RESTRICT)
    contact = models.ForeignKey(verbose_name=_('contact'), to=Contact, on_delete=models.RESTRICT)

    goal = models.CharField(verbose_name=_('goal'), max_length=100,
                            help_text=_('Give a short description of what this request is for'))
    description = models.TextField(verbose_name=_('description'),
                                   help_text=_('Provide more detail on this request, this is your elevator pitch!'))
    internal_notes = models.TextField(verbose_name=_('internal notes'), blank=True,
                                      help_text=_('Internal notes that will NOT be shown publicly'))

    class Meta:
        ordering = ('organisation__name', 'goal')
        verbose_name = _('request')
        verbose_name_plural = _('requests')

    def __str__(self):
        return self.goal


class RequestItem(models.Model):
    OTHER = 0
    HARDWARE = 100
    SOFTWARE = 200
    SERVICE = 300

    TYPE_CHOICES = (
        (OTHER, _('Other')),
        (HARDWARE, _('Hardware')),
        (SOFTWARE, _('Software')),
        (SERVICE, _('Service')),
    )

    request = models.ForeignKey(verbose_name=_('request'), to=Request, on_delete=models.RESTRICT)
    type = models.PositiveIntegerField(verbose_name=_('type'), choices=TYPE_CHOICES, default=OTHER)
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
                                        on_delete=models.CASCADE,
                                        help_text=_('In case there are multiple options to solve your problem'))

    class Meta:
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

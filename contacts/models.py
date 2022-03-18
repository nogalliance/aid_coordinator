from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Organisation(models.Model):
    OTHER = 0

    COMMERCIAL = 100
    ISP = 101

    NON_PROFIT = 200
    ASSOCIATION = 201
    FOUNDATION = 202

    GOVERNMENT = 900
    REGULATOR = 901

    TYPE_CHOICES = (
        (OTHER, _('Other')),
        (_('Commercial'), (
            (COMMERCIAL, _('Commercial (generic)')),
            (ISP, _('Internet Provider'))
        )),
        (_('Non-Profit'), (
            (NON_PROFIT, _('Non-Profit (generic)')),
            (ASSOCIATION, _('Association')),
            (FOUNDATION, _('Foundation')),
        )),
        (_('Governmental'), (
            (GOVERNMENT, _('Government (generic)')),
            (REGULATOR, _('Regulator'))
        )),
    )

    name = models.CharField(verbose_name=_('name'), max_length=100)
    type = models.PositiveIntegerField(verbose_name=_('type'), choices=TYPE_CHOICES, default=OTHER)
    website = models.URLField(verbose_name=_('website'), blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('organisation')
        verbose_name_plural = _('organisations')

    def __str__(self):
        return self.name


class Contact(AbstractUser):
    organisation = models.ForeignKey(verbose_name=_('organisation'), to=Organisation, blank=True, null=True,
                                     on_delete=models.SET_NULL)
    role = models.CharField(verbose_name=_('role'), max_length=50, blank=True)
    phone = models.CharField(verbose_name=_('phone'), max_length=50, blank=True)

    class Meta:
        ordering = ('first_name', 'last_name', 'username')

    def __str__(self):
        if self.first_name or self.last_name:
            name = self.get_full_name()
        else:
            name = self.get_username()

        if self.organisation_id:
            return f"{name} ({self.organisation.name})"
        else:
            return name

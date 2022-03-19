from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrgType(models.IntegerChoices):
    OTHER = 0, _('Other')

    COMMERCIAL = 100, _('Commercial (generic)')
    ISP = 101, _('Internet Provider')
    IXP = 102, _('Internet Exchange')

    NON_PROFIT = 200, _('Non-Profit (generic)')
    ASSOCIATION = 201, _('Association')
    FOUNDATION = 202, _('Foundation')

    EDUCATIONAL = 400, _('Educational (generic)')
    UNIVERSITY = 401, _('University')

    GOVERNMENT = 900, _('Government (generic)')
    REGULATOR = 901, _('Regulator')


class Organisation(models.Model):
    name = models.CharField(verbose_name=_('name'), max_length=100)
    type = models.PositiveIntegerField(verbose_name=_('type'), choices=OrgType.choices, default=OrgType.OTHER)
    website = models.URLField(verbose_name=_('website'), blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('organisation')
        verbose_name_plural = _('organisations')

    def __str__(self):
        return self.name


class Contact(AbstractUser):
    is_staff = True
    organisation = models.ForeignKey(verbose_name=_('organisation'), to=Organisation, blank=True, null=True,
                                     related_name='contacts', on_delete=models.SET_NULL)
    role = models.CharField(verbose_name=_('role'), max_length=50, blank=True)
    phone = models.CharField(verbose_name=_('phone'), max_length=50, blank=True)

    class Meta:
        ordering = ('first_name', 'last_name', 'username')

    def display_name(self):
        if self.first_name or self.last_name:
            return self.get_full_name()
        else:
            return self.get_username()

    def __str__(self):
        if self.organisation_id:
            return f"{self.display_name()} ({self.organisation.name})"
        else:
            return self.display_name()

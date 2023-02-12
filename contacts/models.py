import warnings
from functools import cached_property

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrgType(models.IntegerChoices):
    OTHER = 0, _("Other")

    COMMERCIAL = 100, _("Commercial (generic)")
    ISP = 101, _("Internet Provider")
    IXP = 102, _("Internet Exchange")
    VENDOR = 150, _("Equipment vendor")

    NON_PROFIT = 200, _("Non-Profit (generic)")
    ASSOCIATION = 201, _("Association")
    FOUNDATION = 202, _("Foundation")

    EDUCATIONAL = 400, _("Educational (generic)")
    UNIVERSITY = 401, _("University")

    GOVERNMENT = 900, _("Government (generic)")
    REGULATOR = 901, _("Regulator")


class Organisation(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=100)
    type = models.PositiveIntegerField(verbose_name=_("type"), choices=OrgType.choices, default=OrgType.OTHER)
    listed = models.BooleanField(
        verbose_name=_("listed on website"),
        null=True,
        help_text=_("Shown as a donor organisation on the website"),
    )
    allow_publicity = models.BooleanField(
        verbose_name=_("allow publicity"),
        null=True,
        help_text=_("Shown as a donor organisation in articles, presentations etc."),
    )
    website = models.URLField(verbose_name=_("website"), blank=True)
    logo = models.ImageField(verbose_name=_("logo"), blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = _("organisation")
        verbose_name_plural = _("organisations")

    def __str__(self):
        return self.name


class ContactManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("groups", "organisation")


class Contact(AbstractUser):
    is_staff = True
    organisation = models.ForeignKey(
        verbose_name=_("organisation"),
        to=Organisation,
        blank=True,
        null=True,
        related_name="contacts",
        on_delete=models.SET_NULL,
    )
    requested_organisation = models.CharField(verbose_name=_("requested organisation"), max_length=100, blank=True)
    role = models.CharField(verbose_name=_("role"), max_length=50, blank=True)
    listed = models.BooleanField(
        verbose_name=_("listed on website"),
        null=True,
        help_text=_("Shown as a personal donor on the website"),
    )
    allow_publicity = models.BooleanField(
        verbose_name=_("allow publicity"),
        null=True,
        help_text=_("Shown as a personal donor in articles, presentations etc."),
    )
    phone = models.CharField(verbose_name=_("phone"), max_length=50, blank=True)

    objects = ContactManager()

    def __init__(self, *args, **kwargs):
        is_staff = kwargs.pop("is_staff", True)
        if not is_staff:
            warnings.warn("Contacts are always created as staff")
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")
        ordering = ("first_name", "last_name", "username")

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

    @property
    def group_names(self):
        return [str(group.name).lower() for group in self.groups.all()]

    @property
    def is_donor(self):
        return "donors" in self.group_names

    @property
    def is_requester(self):
        return "requesters" in self.group_names

    @property
    def is_viewer(self):
        return "viewers" in self.group_names

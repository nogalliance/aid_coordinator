from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from contacts.models import Organisation
from supply_demand.models import OfferItem, RequestItem


class EquipmentData(models.Model):
    brand = models.CharField(verbose_name=_("brand"), max_length=50)
    model = models.CharField(verbose_name=_("model"), max_length=100)

    width = models.PositiveIntegerField(verbose_name=_("width"), blank=True, null=True, help_text=_("in cm"))
    height = models.PositiveIntegerField(verbose_name=_("height"), blank=True, null=True, help_text=_("in cm"))
    depth = models.PositiveIntegerField(verbose_name=_("depth"), blank=True, null=True, help_text=_("in cm"))

    weight = models.FloatField(verbose_name=_("weight"), blank=True, null=True, help_text=_("in kg"))

    class Meta:
        unique_together = (("brand", "model"),)
        verbose_name = _("equipment data")
        verbose_name_plural = _("equipment data")

    def __str__(self):
        return f"{self.brand} {self.model}"


class Location(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=100)
    street_address = models.TextField(verbose_name=_("street_address"), blank=True)
    city = models.CharField(verbose_name=_("city"), max_length=50, blank=True)
    postcode = models.CharField(verbose_name=_("postcode"), max_length=16, blank=True)
    country = CountryField(verbose_name=_("country"), blank=True)

    email = models.EmailField(verbose_name=_("email contact"), blank=True)
    phone = PhoneNumberField(verbose_name=_("phone contact"), blank=True)

    is_collection_point = models.BooleanField(
        verbose_name=_("is a collection point"),
        default=False,
        help_text=_("allow donors to send equipment to this location"),
    )
    is_distribution_point = models.BooleanField(
        verbose_name=_("is a distribution point"),
        default=False,
        help_text=_("items at this location " "can be directly assigned to requesters"),
    )

    managed_by = models.ForeignKey(
        verbose_name=_("managed by"),
        to=Organisation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")

    def __str__(self):
        return self.name


class Shipment(models.Model):
    name = models.CharField(verbose_name=_("name"), max_length=100, unique=True)
    when = models.DateField(verbose_name=_("when"), blank=True, null=True)
    current_location = models.ForeignKey(
        verbose_name=_("current location"),
        to=Location,
        on_delete=models.RESTRICT,
        blank=True,
        null=True,
    )
    is_delivered = models.BooleanField(verbose_name=_("is delivered"), default=False)

    class Meta:
        verbose_name = _("shipment")
        verbose_name_plural = _("shipments")

    def __str__(self):
        return self.name


class Claim(models.Model):
    offered_item = models.ForeignKey(verbose_name=_("offered item"), to=OfferItem, on_delete=models.RESTRICT)
    requested_item = models.ForeignKey(
        verbose_name=_("requested item"),
        to=RequestItem,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    amount = models.PositiveIntegerField(
        verbose_name=_("amount"), default=1, help_text=_("The amount of items claimed")
    )
    when = models.DateField(verbose_name=_("when"), auto_now_add=True)
    shipment = models.ForeignKey(
        verbose_name=_("shipment"),
        to=Shipment,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    current_location = models.ForeignKey(
        verbose_name=_("current location"),
        to=Location,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("claim")
        verbose_name_plural = _("claims")

    def __str__(self):
        return f"{self.amount}x {self.offered_item} for request {self.requested_item}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        # If someone claims this, we don't need to reject it anymore
        if self.offered_item.rejected:
            self.offered_item.rejected = False
            self.offered_item.save()

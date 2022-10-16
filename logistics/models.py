from contacts.models import Organisation
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from supply_demand.models import OfferItem


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
    shipment_date = models.DateField(verbose_name=_("shipment date"), blank=True, null=True)
    delivery_date = models.DateField(verbose_name=_("delivery date"), blank=True, null=True)

    is_delivered = models.BooleanField(verbose_name=_("is delivered"), default=False)

    from_location = models.ForeignKey(
        Location,
        verbose_name=_("from location"),
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        related_name="from_location",
    )

    to_location = models.ForeignKey(
        Location,
        verbose_name=_("to location"),
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        related_name="to_location",
    )

    notes = models.TextField(
        verbose_name=_("notes"),
        blank=True,
        help_text=_("Provide details on this shipment"),
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("shipment")
        verbose_name_plural = _("shipments")

    def __str__(self):
        return f"{self.name}({self.from_location} -> {self.to_location})"


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(
        verbose_name=_("shipment"), to=Shipment, blank=True, null=True, on_delete=models.SET_NULL
    )
    offered_item = models.ForeignKey(verbose_name=_("offered item"), to=OfferItem, on_delete=models.RESTRICT)
    amount = models.PositiveIntegerField(
        verbose_name=_("amount"),
        default=1,
        help_text=_("The amount of items claimed"),
        validators=[MinValueValidator(1)],
    )
    # TODO
    when = models.DateField(verbose_name=_("when"), auto_now_add=True)
    last_location = models.ForeignKey(
        Location,
        verbose_name=_("last location"),
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        related_name="last_location",
    )

    parent_shipment_item = models.ForeignKey(
        "self",
        verbose_name=_("parent shipment item"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="sent_items",
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("shipment item")
        verbose_name_plural = _("shipment items")

    def __str__(self):
        return f"{self.amount}x {self.offered_item}"

    @cached_property
    def available(self):
        if not self.parent_shipment_item:
            return self.amount
        parent_amount = self.parent_shipment_item.amount
        return self.parent_shipment_item.sent_items.exclude(id=self.id).aggregate(
            available=parent_amount - Coalesce(Sum("amount"), 0)
        )["available"]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        # validate amount
        if self.amount > self.available:
            raise ValidationError(
                {"amount": _("You can choose max {available} units").format(available=self.available)}
            )


class Item(ShipmentItem):
    class Meta:
        proxy = True

        verbose_name = _("available item")
        verbose_name_plural = _("available items")

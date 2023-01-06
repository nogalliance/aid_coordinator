from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from contacts.models import Contact


class DeliveryMethod(models.IntegerChoices):
    UNKNOWN = 0, _("Unknown")
    SEND_TO_GNA = 100, _("Send to GNA by donor")
    PICKUP_REQUESTED = 200, _("Pickup requested")
    OTHER = 999, _("Other")


class UnusedItemsHandling(models.IntegerChoices):
    CONTACT = 0, _("Contact the donor")
    RETURN = 10, _("Return them to donor")
    DESTROY = 20, _("Destroy them")
    OTHER = 30, _("Donate to another worthy cause")
    SELL = 50, _("Sell them and donate funds to Ukraine")


class ChangeAction(models.IntegerChoices):
    ADD = 1, _("Add")
    CHANGE = 2, _("Change")
    DELETE = 3, _("Delete")


class ChangeType(models.IntegerChoices):
    OFFER = 1, _("Offer")
    REQUEST = 2, _("Request")


class ItemType(models.Model):
    name = models.CharField(verbose_name=_('name'), max_length=50, unique=True)
    order = models.PositiveIntegerField(verbose_name=_('order'), default=50)

    class Meta:
        verbose_name = _('item type')
        verbose_name_plural = _('item types')
        ordering = ('order', 'name')

    def __str__(self):
        return self.name


class RequestManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("items__alternatives__alternatives", "contact__organisation")


class Request(models.Model):
    contact = models.ForeignKey(
        verbose_name=_("contact"),
        to=Contact,
        related_name="requests",
        on_delete=models.RESTRICT,
    )

    goal = models.CharField(
        verbose_name=_("goal"),
        max_length=100,
        help_text=_("Give a short description of what this request is for"),
    )
    description = models.TextField(
        verbose_name=_("description"),
        blank=True,
        help_text=_("Provide more detail on this request, this is your elevator pitch!"),
    )
    internal_notes = models.TextField(
        verbose_name=_("internal notes"),
        blank=True,
        help_text=_("Internal notes that will NOT be shown publicly"),
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    objects = RequestManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_before = None
        self.change_id = None

    class Meta:
        ordering = (
            "contact__organisation__name",
            "contact__last_name",
            "contact__first_name",
            "goal",
        )
        verbose_name = _("request")
        verbose_name_plural = _("requests")

    def __str__(self):
        if self.contact.organisation_id:
            return f"{self.contact.organisation}: {self.goal}"
        else:
            return f"{self.contact}: {self.goal}"

    def change_log_entry(self):
        out = f"Contact: {self.contact}"
        out += f"\nGoal: {self.goal}"
        out += f"\nDescription:\n{self.description}"
        out += "\nItems:"
        if self.pk:
            for item in RequestItem.objects.filter(request_id=self.pk):
                out += f"\n- {item}"
        return out

    def save(self, *args, **kwargs):
        self.change_id = self.pk
        self.change_before = Request.objects.get(pk=self.pk).change_log_entry() if self.pk else ""

        super().save(*args, **kwargs)


class RequestItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("request__contact__organisation")


class RequestItem(models.Model):
    request = models.ForeignKey(
        verbose_name=_("request"),
        to=Request,
        related_name="items",
        on_delete=models.CASCADE,
    )
    type = models.ForeignKey(verbose_name=_('type'), to=ItemType, on_delete=models.RESTRICT)
    brand = models.CharField(
        verbose_name=_("brand"),
        max_length=50,
        blank=True,
        help_text=_("Either a brand name or a description of the kind of brand"),
    )
    model = models.CharField(
        verbose_name=_("model"),
        max_length=100,
        blank=True,
        help_text=_("Either an explicit model or a description of the required features"),
    )
    amount = models.PositiveIntegerField(
        verbose_name=_("# required"),
        default=1,
        help_text=_("The minimal amount that you need"),
    )
    up_to = models.PositiveIntegerField(
        verbose_name=_("up to"),
        blank=True,
        null=True,
        help_text=_("The maximum amount that you could use"),
    )

    notes = models.CharField(
        verbose_name=_("notes"),
        max_length=250,
        blank=True,
        help_text=_("Any extra information that can help a donor decide if they have something " "that can help you"),
    )
    alternative_for = models.ForeignKey(
        verbose_name=_("alternative for"),
        to="RequestItem",
        blank=True,
        null=True,
        related_name="alternatives",
        on_delete=models.CASCADE,
        help_text=_("In case there are multiple options to solve your problem"),
    )
    offered_items = models.ManyToManyField("OfferItem", through="Claim", related_name="requested_items")

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    objects = RequestItemManager()

    class Meta:
        ordering = ("type", "brand", "model")
        verbose_name = _("requested item")
        verbose_name_plural = _("requested items")

    def __str__(self):
        return f"{self.brand} {self.model}".strip()

    @property
    def counted_name(self):
        if self.up_to:
            return f"{self.up_to}x {self.brand} {self.model}".replace("  ", " ")
        return f"{self.amount}x {self.brand} {self.model}".replace("  ", " ")

    @cached_property
    def assigned(self):
        return self.claim_set.aggregate(assigned=Coalesce(Sum("amount"), 0))["assigned"]

    @cached_property
    def needed(self):
        if self.up_to:
            return self.up_to - self.assigned
        return self.amount - self.assigned

    def clean(self):
        super().clean()

        if self.alternative_for_id and self.id:
            if self.alternative_for_id == self.id:
                raise ValidationError({"alternative_for": "An item can't be an alternative for itself"})

            alt = self.alternative_for
            while alt:
                if alt.id == self.id:
                    raise ValidationError({"alternative_for": "Alternatives can't form a loop"})
                alt = alt.alternative_for if alt.alternative_for_id else None

        if self.amount == self.up_to:
            self.up_to = None


class OfferManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("items", "contact__organisation")


class Offer(models.Model):
    contact = models.ForeignKey(
        verbose_name=_("contact"),
        to=Contact,
        related_name="offers",
        on_delete=models.RESTRICT,
    )
    description = models.CharField(
        verbose_name=_("description"),
        max_length=100,
        blank=True,
        help_text=_("Give a short description of what this offer is"),
    )
    location = models.TextField(
        verbose_name=_("location"),
        blank=True,
        help_text=_("Where is the equipment coming from?"),
    )
    delivery_method = models.PositiveIntegerField(
        verbose_name=_("delivery method"),
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.UNKNOWN,
    )
    unused_item_handling = models.PositiveIntegerField(
        verbose_name=_("unused item handling"),
        choices=UnusedItemsHandling.choices,
        default=UnusedItemsHandling.CONTACT,
        help_text=_(
            "If we can't find a Ukrainian organisation that can "
            "use these items in a reasonable time, what should "
            "we do with them?"
        ),
    )
    internal_notes = models.TextField(
        verbose_name=_("internal notes"),
        blank=True,
        help_text=_("Internal notes that will NOT be shown publicly"),
    )

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    objects = OfferManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_before = None
        self.change_id = None

    class Meta:
        ordering = (
            "description",
            "contact__organisation__name",
            "contact__first_name",
            "contact__last_name",
        )
        verbose_name = _("offer")
        verbose_name_plural = _("offers")

    def __str__(self):
        if self.contact.organisation_id:
            return f"{self.contact.organisation}: {self.description}"
        else:
            return f"{self.contact}: {self.description}"

    def change_log_entry(self):
        out = f"Contact: {self.contact}"
        if self.location:
            out += f"\nLocation:\n{self.location}"
        out += f"\nDelivery method: {self.get_delivery_method_display()}"
        out += "\nItems:"
        if self.pk:
            for item in OfferItem.objects.filter(offer_id=self.pk):
                out += f"\n- {item}"
        return out

    def save(self, *args, **kwargs):
        self.change_id = self.pk
        self.change_before = Offer.objects.get(pk=self.pk).change_log_entry() if self.pk else ""

        super().save(*args, **kwargs)


class OfferItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("offer__contact__organisation")


class OfferItem(models.Model):
    offer = models.ForeignKey(
        verbose_name=_("offer"),
        to=Offer,
        related_name="items",
        on_delete=models.CASCADE,
    )
    type = models.ForeignKey(verbose_name=_('type'), to=ItemType, on_delete=models.RESTRICT)
    brand = models.CharField(verbose_name=_("brand"), max_length=50, blank=True)
    model = models.CharField(verbose_name=_("model"), max_length=100)
    amount = models.PositiveIntegerField(verbose_name=_("# offered"), null=True, blank=True)
    notes = models.CharField(
        verbose_name=_("notes"),
        max_length=250,
        blank=True,
        help_text=_("Any extra information that can help a requester decide if they can use this"),
    )

    equipment_data = models.ForeignKey(
        "logistics.EquipmentData",
        verbose_name=_("equipment data"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    rejected = models.BooleanField(verbose_name=_("rejected"), default=False)

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    objects = OfferItemManager()

    _claimed = None

    class Meta:
        ordering = ("type", "brand", "model")
        verbose_name = _("offered item")
        verbose_name_plural = _("offered items")

    def __str__(self):
        return f"{self.brand} {self.model}".strip()

    @property
    def counted_name(self):
        if self.amount:
            return f"{self.amount}x {self.brand} {self.model}".replace("  ", " ")

        return f"{_('Multiple')} {self.brand} {self.model}".replace("  ", " ")

    @property
    def claimed(self):
        if self._claimed is not None:
            return self._claimed

        return self.claim_set.aggregate(Sum("amount"))["amount__sum"] or 0

    @claimed.setter
    def claimed(self, value: bool):
        self._claimed = value or 0

    @cached_property
    def available(self):
        if not self.amount:
            return 10

        return self.amount - self.claimed


class ChangeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("who__organisation")


class Change(models.Model):
    when = models.DateTimeField(verbose_name=_("when"), auto_now_add=True)
    who = models.ForeignKey(
        verbose_name=_("who"),
        to=Contact,
        on_delete=models.RESTRICT,
        related_name="changes",
    )
    action = models.PositiveIntegerField(verbose_name=_("action"), choices=ChangeAction.choices)
    type = models.PositiveIntegerField(verbose_name=_("type"), choices=ChangeType.choices)
    what = models.CharField(verbose_name=_("what"), max_length=250)
    before = models.TextField(verbose_name=_("before"), blank=True)
    after = models.TextField(verbose_name=_("after"), blank=True)

    objects = ChangeManager()

    class Meta:
        ordering = ("when", "who")
        verbose_name = _("change")
        verbose_name_plural = _("changes")

    def __str__(self):
        if self.action == ChangeAction.ADD:
            action = _("added")
        elif self.action == ChangeAction.CHANGE:
            action = _("changed")
        elif self.action == ChangeAction.DELETE:
            action = _("removed")
        else:
            action = _("did something to")

        return f"{self.who.display_name()} {action} {self.get_type_display().lower()} {_('of')} {self.what}"


class Claim(models.Model):
    offered_item = models.ForeignKey(
        verbose_name=_("offered item"),
        to=OfferItem,
        on_delete=models.RESTRICT,
    )
    requested_item = models.ForeignKey(
        verbose_name=_("requested item"),
        to=RequestItem,
        on_delete=models.RESTRICT,
    )
    amount = models.PositiveIntegerField(
        verbose_name=_("amount"),
        default=1,
        help_text=_("The amount of items claimed"),
    )

    when = models.DateField(verbose_name=_("when"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)

    notes = models.TextField(
        verbose_name=_("notes"),
        blank=True,
        help_text=_("Any extra information related to claim"),
    )

    class Meta:
        verbose_name = _("claim")
        verbose_name_plural = _("claims")

    def __str__(self):
        return f"{self.amount}x {self.offered_item}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        # If someone claims this, we don't need to reject it anymore
        if self.offered_item.rejected:
            self.offered_item.rejected = False
            self.offered_item.save()

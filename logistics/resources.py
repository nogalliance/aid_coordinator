from import_export import fields, resources
from import_export.widgets import IntegerWidget

from logistics.models import EquipmentData, ShipmentItem


class EquipmentDataResource(resources.ModelResource):
    class Meta:
        model = EquipmentData
        fields = ("brand", "model", "width", "height", "depth", "weight")
        import_id_fields = ("brand", "model")


class ShipmentItemExportResource(resources.ModelResource):
    type = fields.Field(attribute="offered_item__type__name")
    brand = fields.Field(attribute="offered_item__brand")
    model = fields.Field(attribute="offered_item__model")
    amount = fields.Field(attribute="amount", widget=IntegerWidget())
    shipment = fields.Field(attribute="shipment")
    from_location = fields.Field(attribute="shipment__from_location")
    to_location = fields.Field(attribute="shipment__to_location")
    status = fields.Field(attribute="shipment__get_status_display")

    donor_first_name = fields.Field(attribute="offered_item__offer__contact__first_name")
    donor_last_name = fields.Field(attribute="offered_item__offer__contact__last_name")
    donor_email = fields.Field(attribute="offered_item__offer__contact__email")
    donor_organisation = fields.Field(attribute="offered_item__offer__contact__organisation__name")

    class Meta:
        model = ShipmentItem
        fields = (
            "type",
            "brand",
            "model",
            "amount",
            "shipment",
            "from_location",
            "to_location",
            "status",
            "donor_first_name",
            "donor_last_name",
            "donor_email",
            "donor_organisation",
        )


class ItemExportResource(ShipmentItemExportResource):
    amount = fields.Field(attribute="available", widget=IntegerWidget())

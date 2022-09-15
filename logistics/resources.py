from import_export import resources

from logistics.models import EquipmentData


class EquipmentDataResource(resources.ModelResource):
    class Meta:
        model = EquipmentData
        fields = ("brand", "model", "width", "height", "depth", "weight")
        import_id_fields = ("brand", "model")

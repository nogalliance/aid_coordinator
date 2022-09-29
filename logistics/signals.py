from django.db.models.signals import pre_save
from django.dispatch import receiver
from logistics.models import Shipment


@receiver(pre_save, sender=Shipment)
def set_shipment_item_location(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if (
            not obj.is_delivered == instance.is_delivered
            or not obj.to_location == instance.to_location
            or not obj.from_location == instance.from_location
        ):
            if instance.is_delivered:
                instance.shipmentitem_set.update(last_location=instance.to_location)
            else:
                instance.shipmentitem_set.update(last_location=instance.from_location)

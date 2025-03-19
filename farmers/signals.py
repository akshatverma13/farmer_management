from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Farmer
from .tasks import increment_block_farmer_count

@receiver(post_save, sender=Farmer)
def farmer_added(sender, instance, created, **kwargs):
    if created:
        increment_block_farmer_count.delay(instance.block_id)
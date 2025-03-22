from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Farmer
from .tasks import update_daily_farmer_counts, increment_block_farmer_count

@receiver(post_save, sender=Farmer)
def farmer_added(sender, instance, created, **kwargs):
    if created:
        date_str = instance.created_at.date().isoformat()
        month_str = instance.created_at.strftime('%Y-%m')
        # Trigger daily and monthly count updates
        update_daily_farmer_counts.delay(instance.surveyor_id, date_str, month_str)
        increment_block_farmer_count.delay(instance.block_id, date_str, month_str)
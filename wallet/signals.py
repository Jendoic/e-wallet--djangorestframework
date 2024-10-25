from django.db.models.signals import post_save
from django.dispatch import receiver

from auths.models import CustomUser as User
from .models import Wallet

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

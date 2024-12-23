from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, BankAccount

@receiver(post_save, sender=CustomUser)
def create_bank_account(sender, instance, created, **kwargs):
    if created:
        # Usa `get_or_create` para evitar duplicados
        BankAccount.objects.get_or_create(user=instance)
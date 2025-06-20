import random
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from django.contrib.auth.models import User

def generate_unique_account_number():
    while True:
        number = str(random.randint(100_000_000_000, 999_999_999_999))
        if not Profile.objects.filter(account_number=number).exists():
            return number

@receiver (post_save, sender=User)
def create_bank_account(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, account_number=generate_unique_account_number())

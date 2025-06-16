from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=12)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal(0.00))
    create_at = models.DateTimeField(auto_now_add=True)


    def __st__(self):
        return f'{self.user} Profile'
    
class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    TYPE = (
        ('Send', 'Send'),
        ('Load', 'Load'),
        ('Transfer', 'Transfer'),
        ('Bills', 'Bills'),
        ('Gsave', 'Gsave'),
        ('Ginvest', 'Ginvest'),
        ('Borrows', 'Borrows'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=12, choices=TYPE)
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    date_time = models.DateTimeField(auto_now_add=True)


    def __st__(self):
        return f'{self.transaction_type} of {self.amount} by {self.user}'
    
class Transfer(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    account_number = models.PositiveIntegerField()
    account_name = models.CharField(max_length=800)
    bank = models.CharField(max_length=800)
    proof_of_payment = models.FileField(upload_to='Tranfers/')
    date_time = models.DateTimeField(auto_now_add=True)

    def __st__(self):        
        return f'transfer by {self.transaction.user}'
    

class Send(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    reciever = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    date_time = models.DateTimeField(auto_now_add=True)


    def __st__(self):
        return f'Fund sent by {self.transaction.user} to {self.reciever}'
    


class VerificationCode(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    code = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    expired = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Verification Code'
        verbose_name_plural = 'Verification Codes'
        ordering = ['-created_at']

    def __st__(self):
        return f'Verification code of {self.transaction.transaction_type} by {self.transaction.user}'

    def check_validity(self, expiry_minutes=10):
        """
        Checks if the code is expired based on created_at timestamp.
        Updates the `expired` field accordingly.
        Returns True if still valid, False if expired.
        """
        now = timezone.now()
        expiry_time = self.created_at + timedelta(minutes=expiry_minutes)

        if now > expiry_time:
            self.expired = True
        else:
            self.expired = False

        self.save(update_fields=['expired'])
        return not self.expired

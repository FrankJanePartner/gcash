from django.contrib import admin
from django.contrib.auth.models import Group
from .models import  Profile, Transaction, Transfer, Send, VerificationCode

# Register your models here.
admin.site.register(Profile)
admin.site.register(Transaction)
admin.site.register(Transfer)
admin.site.register(Send)
admin.site.register(VerificationCode)

admin.site.unregister(Group)
from .models import Profile, Transaction, Transfer, Send, VerificationCode
from django.contrib.auth.models import User
# import requests

def globalContext(request):
    user = request.user
    if user.is_authenticated:
        profile = Profile.objects.filter(user=user).first()  # Retrieve the profile
        if profile:
            balance = profile.balance
            context = {
                'balance' : balance,
                'profile' : profile
            }
        else:
            balance = 0.00
            context = {
                'balance' : balance
            }
    else:
        balance = 0.00
        
        context = {
            'balance' : balance
        }

    return context
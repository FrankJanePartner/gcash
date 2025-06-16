from django.urls import path
from .views import home, dashboard, send, sendTwo, lookup_account_name, transfer, transferTwo, success, amen

app_name = 'core'
urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('send/', send, name='send'),
    path('send-two/', sendTwo, name='send-two'),
    path('lookup/', lookup_account_name, name='lookup'),
    path('transfer/', transfer, name='transfer'),
    path('transfer-two/', transferTwo, name='transfer-two'),
    path('success/', success, name='success'),
    path('amen/', amen, name='amen'),
]

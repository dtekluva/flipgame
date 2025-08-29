"""
URL configuration for Bomb Flip Betting Game backend
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('game_ledger.urls')),
]

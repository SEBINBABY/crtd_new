from django.contrib import admin
from .models import OTP, Passkey

# Register your models here.

admin.site.register(OTP)
admin.site.register(Passkey)

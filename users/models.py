from django.db import models
from django.utils.timezone import now, timedelta

class Passkey(models.Model):
    key = models.CharField(max_length=255)  # Company passkey
    is_active = models.BooleanField(default=True)


class OTP(models.Model):
    email = models.EmailField()  # Store email associated with the OTP
    full_name = models.CharField(max_length=100)
    otp_code = models.CharField(max_length=6)  # Store the OTP code
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when OTP was created

    def is_expired(self):
        valid_duration = timedelta(minutes=10)
        expiration_time = self.created_at + valid_duration
        current_time = now()
        print(f"Current time: {current_time}, Expiration time: {expiration_time}")
        return current_time > expiration_time


    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"



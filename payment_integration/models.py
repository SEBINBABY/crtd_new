from django.db import models
from admin_dashboard.models import User

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    razorpay_order_id = models.CharField(max_length=255, unique=True)  # Razorpay order ID
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)  # Razorpay payment ID
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)  # Razorpay Signature
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in INR
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for updates

    def __str__(self):
        return f"Payment {self.razorpay_order_id} - {self.status}"


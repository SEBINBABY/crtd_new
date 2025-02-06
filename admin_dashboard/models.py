from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from django.core.validators import RegexValidator
from django.db.models import Q
from quiz.models import Result
from django.utils.timezone import now
import datetime

from django.utils.timezone import localtime

class User(AbstractBaseUser, PermissionsMixin):
    USER = 'user'
    HR_STAFF = 'hr_staff'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (USER,'User'),
        (HR_STAFF,'HR_Staff'),
        (ADMIN, 'Admin')
        ]
    
    email = models.EmailField(null=False, blank=False, unique=True)
    username = models.CharField(max_length=50, blank=False, null=False)
    contact_number = models.CharField(max_length=15, validators=[RegexValidator(
                                        regex=r'^\d{10}$',
                                        message="Contact number must be exactly 10 digits and contain only numbers."
                                        )])
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_qualified = models.BooleanField(default=True)
    has_quit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    tcn_number = models.CharField(max_length=8, null=True, blank=True)
    has_paid = models.BooleanField(default=False,blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def is_hr_staff(self):
        return self.role == self.HR_STAFF
    
    def is_admin(self):
        return self.role == self.ADMIN
    
    def is_user(self):
        return self.role == self.USER

    def _str_(self):
        return self.email 
    
    def serialize(self):
        test_status = ""
        time_limit = datetime.timedelta(minutes=25)
        test_started = Result.objects.filter(Q(user=self,end_time__isnull=True,start_time__gte = now() - time_limit) 
                        | Q(user=self,user__is_verified=False,end_time__gte = now() - datetime.timedelta(hours=2,minutes=15))).exists()
    

        if self.is_verified:
            test_status = "Submitted"
        elif self.has_quit:
            test_status = "Quit"
        elif not self.is_qualified:
            test_status = "Disqualified"
        elif self.user_results.count() == 0:
            test_status = "Not Started"
        elif test_started and self.is_qualified and not self.is_verified:
            test_status = "In Progress"
        else:
            test_status = "Closed Test"
        


        payment_status = "Paid" if (self.paid) else "Not Paid"

        data = {
            "id": self.id,
            "Full Name": self.username,
            "E-mail": self.email,
            "Contact": self.contact_number,
            "Account Creation Date": f"{localtime(self.created_at):%d/%m/%Y %H:%M}",
            "TCN Number": self.tcn_number,
            "Test Status": test_status,
            "Payment Status": payment_status,
        }
        return data
    


class Amount(models.Model):
    value = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Amount: {self.value}"
    
    def get_amount():
        amount_obj = Amount.objects.first()
        if amount_obj:
            return amount_obj.value
        else:
            return 1  # default value if no Amount record is found
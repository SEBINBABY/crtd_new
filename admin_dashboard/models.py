from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager

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
    contact_number = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    tcn_number = models.CharField(max_length=10, null=True, blank=True)
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
    


class Amount(models.Model):
    """
    Singleton model to store a single Amount value.
    """
    value = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Amount: {self.value}"
    
    def save(self, *args, **kwargs):
        self.id = 1  # Force id=1
        super().save(*args, **kwargs)

    @classmethod
    def get_value(cls):
        """
        Returns the single Amount instance's value, creating it if it doesn't exist.
        """
        obj, _ = cls.objects.get_or_create(id=1)
        return obj.value    

    @classmethod
    def set_value(cls,amount):
        """
        Sets the single Amount instance's value.
        """
        obj, _ = cls.objects.get_or_create(id=1)
        obj.value = amount
        obj.save()

    

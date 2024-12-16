from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Email is required")

        user = self.model(
            email=self.normalize_email(email),
            username=kwargs.get('username', ''),
            contact_number=kwargs.get('contact_number', ''),  # Handle contact_number
        )

        # Set the password (hashed)
        user.set_password(password)
        user.role = self.model.USER  # Set the role as USER
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=kwargs.get('username', '')
        )
        user.first_name = kwargs.get('first_name')
        user.last_name = kwargs.get('last_name')
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.role = self.model.ADMIN  # Set the role as ADMIN
        user.save(using=self._db)
        return

    def authenticate(self, email=None, password=None, **kwargs):
        """
        Authenticate a user by email and password.
        """
        try:
            user = self.model.objects.get(email=email)
            if user.check_password(password):
                return user
        except self.model.DoesNotExist:
            return None
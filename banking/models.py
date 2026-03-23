from django.db import models
from django.contrib.auth.hashers import make_password

class UserData(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.password.startswith("pbkdf2"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    sender = models.ForeignKey(UserData, related_name="sent", on_delete=models.CASCADE)
    receiver = models.ForeignKey(UserData, related_name="received", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="SUCCESS")
    timestamp = models.DateTimeField(auto_now_add=True)
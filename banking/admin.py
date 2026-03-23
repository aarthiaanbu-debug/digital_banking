from django.contrib import admin
from .models import UserData, Transaction

admin.site.register(UserData)
admin.site.register(Transaction)
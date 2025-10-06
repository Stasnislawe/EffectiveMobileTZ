from django.contrib import admin
from .models import Role, UserRole, User, BusinessElement

# Register your models here.

admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserRole)
admin.site.register(BusinessElement)


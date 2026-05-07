from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ('phone_number',)
    list_display = ('phone_number', 'nickname', 'role', 'is_active', 'is_cancelled', 'is_staff')
    list_filter = ('role', 'is_active', 'is_cancelled', 'is_staff')
    search_fields = ('phone_number', 'nickname')

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('个人信息', {'fields': ('nickname', 'role')}),
        ('权限', {'fields': ('is_active', 'is_cancelled', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('phone_number', 'nickname', 'role', 'password1', 'password2'),
            },
        ),
    )

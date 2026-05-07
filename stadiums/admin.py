from django.contrib import admin

from .models import Stadium


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'audit_status', 'is_open', 'deletion_requested', 'updated_at')
    list_filter = ('audit_status', 'is_open', 'deletion_requested')
    search_fields = ('name', 'address', 'phone_number', 'owner__phone_number')

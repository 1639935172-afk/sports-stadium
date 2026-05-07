from django.contrib import admin

from .models import Field, Stadium, TimeSlot


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'audit_status', 'is_open', 'deletion_requested', 'updated_at')
    list_filter = ('audit_status', 'is_open', 'deletion_requested')
    search_fields = ('name', 'address', 'phone_number', 'owner__phone_number')


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('number', 'stadium', 'field_type', 'price_per_hour', 'is_active', 'updated_at')
    list_filter = ('field_type', 'is_active')
    search_fields = ('number', 'stadium__name')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('field', 'date', 'start_time', 'end_time', 'is_available', 'updated_at')
    list_filter = ('date', 'is_available')
    search_fields = ('field__number', 'field__stadium__name')

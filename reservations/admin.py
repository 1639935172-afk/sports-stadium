from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'time_slot', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = (
        'user__phone_number',
        'time_slot__field__number',
        'time_slot__field__stadium__name',
    )

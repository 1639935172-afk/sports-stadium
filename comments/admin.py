from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('stadium', 'user', 'audit_status', 'created_at')
    list_filter = ('audit_status', 'created_at')
    search_fields = ('content', 'stadium__name', 'user__phone_number', 'user__nickname')

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import UserRole
from stadiums.models import StadiumAuditStatus, TimeSlot


class ReservationStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')
    CANCELLED = 'cancelled', _('已取消')


class Reservation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='用户',
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='预约时段',
    )
    status = models.CharField(
        '预约状态',
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '预约'
        verbose_name_plural = '预约'

    def __str__(self):
        return f'{self.user} - {self.time_slot}'

    def clean(self):
        if self.user_id and self.user.role != UserRole.ORDINARY:
            raise ValidationError('只有普通用户可以提交预约')

        if not self.time_slot_id:
            return

        field = self.time_slot.field
        stadium = field.stadium
        if (
            stadium.audit_status != StadiumAuditStatus.APPROVED
            or not stadium.is_open
            or stadium.deletion_requested
        ):
            raise ValidationError('该场馆当前不可预约')
        if not field.is_active:
            raise ValidationError('该场地当前不可预约')
        if not self.time_slot.is_available:
            raise ValidationError('该时段当前不可预约')

        if self.user_id:
            existing_reservations = Reservation.objects.filter(
                user=self.user,
                time_slot=self.time_slot,
                status__in=[ReservationStatus.PENDING, ReservationStatus.APPROVED],
            )
            if self.pk:
                existing_reservations = existing_reservations.exclude(pk=self.pk)
            if existing_reservations.exists():
                raise ValidationError('你已经提交过该时段的预约')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

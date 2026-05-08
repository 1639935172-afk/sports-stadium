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

    @staticmethod
    def occupying_statuses():
        return [ReservationStatus.PENDING, ReservationStatus.APPROVED]

    def _occupying_conflicts(self):
        reservations = Reservation.objects.filter(
            time_slot=self.time_slot,
            status__in=self.occupying_statuses(),
        )
        if self.pk:
            reservations = reservations.exclude(pk=self.pk)
        return reservations

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

        if self.status in self.occupying_statuses() and self._occupying_conflicts().exists():
            raise ValidationError('该时段已有待审核或已通过的预约')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self):
        if self._occupying_conflicts().exists():
            raise ValidationError('该时段已有待审核或已通过的预约')
        self.status = ReservationStatus.APPROVED
        self.save(update_fields=['status', 'updated_at'])

    def reject(self):
        self.status = ReservationStatus.REJECTED
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self):
        if self.status not in [ReservationStatus.PENDING, ReservationStatus.APPROVED]:
            raise ValidationError('只有待审核或已通过的预约可以取消')
        self.status = ReservationStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])

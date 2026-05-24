from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

from accounts.models import UserRole
from stadiums.models import StadiumAuditStatus, TimeSlot


# 预约状态：用户先创建待支付预约，支付成功后才进入场馆管理员审核。
class ReservationStatus(models.TextChoices):
    AWAITING_PAYMENT = 'awaiting_payment', _('待支付')
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')
    CANCELLED = 'cancelled', _('已取消')
    PAYMENT_FAILED = 'payment_failed', _('支付失败')


class PaymentStatus(models.TextChoices):
    UNPAID = 'unpaid', _('待支付')
    PAID = 'paid', _('已支付')
    FAILED = 'failed', _('支付失败')
    CLOSED = 'closed', _('已关闭')
    REFUNDED = 'refunded', _('已退款')


# 预约表：记录“哪个普通用户预约了哪个时段”。
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
        default=ReservationStatus.AWAITING_PAYMENT,
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
        # 这些状态会实际占用时段，后续预约需要避开它们。
        return [
            ReservationStatus.AWAITING_PAYMENT,
            ReservationStatus.PENDING,
            ReservationStatus.APPROVED,
        ]

    def _occupying_conflicts(self):
        # 查找同一时段下已经占用资源的预约记录。
        reservations = Reservation.objects.filter(
            time_slot=self.time_slot,
            status__in=self.occupying_statuses(),
        )
        if self.pk:
            reservations = reservations.exclude(pk=self.pk)
        return reservations

    @property
    def is_expired(self):
        slot_start_at = timezone.make_aware(
            timezone.datetime.combine(self.time_slot.date, self.time_slot.start_time),
            timezone.get_current_timezone(),
        )
        return slot_start_at <= timezone.localtime()

    def clean(self):
        # 只有普通用户可以发起预约。
        if self.user_id and self.user.role != UserRole.ORDINARY:
            raise ValidationError('只有普通用户可以提交预约')

        if not self.time_slot_id:
            return

        # 预约前要同时检查场馆、场地、时段三层状态。
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

        if self.status in self.occupying_statuses() and self.is_expired:
            raise ValidationError('该时段已过期，不能预约')

        # 待支付、待审核和已通过都算占用，同一时段不能出现第二条占用态预约。
        if self.status in self.occupying_statuses() and self._occupying_conflicts().exists():
            raise ValidationError('该时段已有待支付、待审核或已通过的预约')

    def save(self, *args, **kwargs):
        # 正常保存预约时统一先跑模型校验。
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self):
        # 审核通过前再次检查冲突，避免并发或状态变化导致重复占用。
        if self._occupying_conflicts().exists():
            raise ValidationError('该时段已有待审核或已通过的预约')
        self.status = ReservationStatus.APPROVED
        self.save(update_fields=['status', 'updated_at'])

    def reject(self):
        # 拒绝预约只改变状态，不删除记录。
        self.status = ReservationStatus.REJECTED
        self.save(update_fields=['status', 'updated_at'])
        if hasattr(self, 'payment') and self.payment.status == PaymentStatus.PAID:
            self.payment.refund()

    def cancel(self):
        # 只有仍在流程中的预约才允许取消。
        if self.status not in [
            ReservationStatus.AWAITING_PAYMENT,
            ReservationStatus.PENDING,
            ReservationStatus.APPROVED,
        ]:
            raise ValidationError('只有待支付、待审核或已通过的预约可以取消')
        if self.is_expired:
            raise ValidationError('已过期的预约不能取消')
        self.status = ReservationStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
        if hasattr(self, 'payment'):
            if self.payment.status == PaymentStatus.PAID:
                self.payment.refund()
            elif self.payment.status == PaymentStatus.UNPAID:
                self.payment.close()

    def ensure_payment(self):
        payment, _ = Payment.objects.get_or_create(
            reservation=self,
            defaults={'amount': self.time_slot.field.price_per_hour},
        )
        return payment

    def mark_payment_paid(self):
        if self.status != ReservationStatus.AWAITING_PAYMENT:
            raise ValidationError('只有待支付预约可以支付')
        if self.is_expired:
            self.mark_payment_failed()
            raise ValidationError('该时段已过期，支付失败')
        payment = self.ensure_payment()
        payment.mark_paid()
        self.status = ReservationStatus.PENDING
        self.save(update_fields=['status', 'updated_at'])

    def mark_payment_failed(self):
        if self.status != ReservationStatus.AWAITING_PAYMENT:
            raise ValidationError('只有待支付预约可以标记支付失败')
        payment = self.ensure_payment()
        payment.mark_failed()
        self.status = ReservationStatus.PAYMENT_FAILED
        self.save(update_fields=['status', 'updated_at'])


class Payment(models.Model):
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='预约',
    )
    payment_no = models.CharField('支付流水号', max_length=40, unique=True, blank=True)
    amount = models.DecimalField('支付金额', max_digits=8, decimal_places=2)
    status = models.CharField(
        '支付状态',
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    paid_at = models.DateTimeField('支付时间', null=True, blank=True)
    closed_at = models.DateTimeField('关闭时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '支付单'
        verbose_name_plural = '支付单'

    def __str__(self):
        return f'{self.payment_no} - {self.amount}'

    def save(self, *args, **kwargs):
        if not self.payment_no:
            self.payment_no = uuid4().hex
        return super().save(*args, **kwargs)

    def mark_paid(self):
        if self.status != PaymentStatus.UNPAID:
            raise ValidationError('只有待支付订单可以支付')
        self.status = PaymentStatus.PAID
        self.paid_at = timezone.localtime()
        self.closed_at = None
        self.save(update_fields=['status', 'paid_at', 'closed_at', 'updated_at'])

    def mark_failed(self):
        if self.status != PaymentStatus.UNPAID:
            raise ValidationError('只有待支付订单可以标记失败')
        self.status = PaymentStatus.FAILED
        self.closed_at = timezone.localtime()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])

    def close(self):
        if self.status != PaymentStatus.UNPAID:
            return
        self.status = PaymentStatus.CLOSED
        self.closed_at = timezone.localtime()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])

    def refund(self):
        if self.status != PaymentStatus.PAID:
            return
        self.status = PaymentStatus.REFUNDED
        self.closed_at = timezone.localtime()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])

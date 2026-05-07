from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import UserRole


class StadiumAuditStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('通过')
    REJECTED = 'rejected', _('不通过')


class Stadium(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stadiums',
        verbose_name='场馆管理员',
    )
    name = models.CharField('场馆名称', max_length=100)
    address = models.CharField('场馆地址', max_length=255)
    phone_number = models.CharField('联系电话', max_length=20)
    information = models.TextField('场馆简介', blank=True)
    audit_status = models.CharField(
        '审核状态',
        max_length=20,
        choices=StadiumAuditStatus.choices,
        default=StadiumAuditStatus.PENDING,
    )
    is_open = models.BooleanField('开放状态', default=False)
    deletion_requested = models.BooleanField('申请删除', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '体育场馆'
        verbose_name_plural = '体育场馆'

    def __str__(self):
        return self.name

    def clean(self):
        if self.owner_id and self.owner.role != UserRole.STADIUM_ADMIN:
            raise ValidationError('只有场馆管理员可以负责场馆')

    def submit_for_review(self):
        self.audit_status = StadiumAuditStatus.PENDING
        self.is_open = False
        self.save(update_fields=['audit_status', 'is_open', 'updated_at'])

    def request_deletion(self):
        self.deletion_requested = True
        self.audit_status = StadiumAuditStatus.PENDING
        self.save(update_fields=['deletion_requested', 'audit_status', 'updated_at'])

    def approve(self):
        if self.deletion_requested:
            self.delete()
            return 'deleted'

        self.audit_status = StadiumAuditStatus.APPROVED
        self.is_open = True
        self.save(update_fields=['audit_status', 'is_open', 'updated_at'])
        return 'approved'

    def reject(self):
        if self.deletion_requested:
            self.deletion_requested = False
            self.audit_status = StadiumAuditStatus.APPROVED
            self.is_open = True
        else:
            self.audit_status = StadiumAuditStatus.REJECTED
            self.is_open = False
        self.save(update_fields=['deletion_requested', 'audit_status', 'is_open', 'updated_at'])

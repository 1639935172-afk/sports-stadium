from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import UserRole
from stadiums.models import Stadium, StadiumAuditStatus


class CommentAuditStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('已通过')
    REJECTED = 'rejected', _('已拒绝')


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='用户',
    )
    stadium = models.ForeignKey(
        Stadium,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='场馆',
    )
    content = models.TextField('评论内容')
    audit_status = models.CharField(
        '审核状态',
        max_length=20,
        choices=CommentAuditStatus.choices,
        default=CommentAuditStatus.PENDING,
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '评论'
        verbose_name_plural = '评论'

    def __str__(self):
        return f'{self.user} - {self.stadium}'

    def clean(self):
        if self.user_id and self.user.role != UserRole.ORDINARY:
            raise ValidationError('只有普通用户可以提交评论')

        if self.stadium_id and (
            self.stadium.audit_status != StadiumAuditStatus.APPROVED
            or not self.stadium.is_open
            or self.stadium.deletion_requested
        ):
            raise ValidationError('只能评论公开开放的场馆')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self):
        self.audit_status = CommentAuditStatus.APPROVED
        self.save(update_fields=['audit_status', 'updated_at'])

    def reject(self):
        self.audit_status = CommentAuditStatus.REJECTED
        self.save(update_fields=['audit_status', 'updated_at'])

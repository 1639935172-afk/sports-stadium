from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from accounts.models import UserRole


# 场馆审核状态：新建、修改、删除申请都会围绕这组状态流转。


class StadiumAuditStatus(models.TextChoices):
    PENDING = 'pending', _('待审核')
    APPROVED = 'approved', _('通过')
    REJECTED = 'rejected', _('不通过')


# 场馆联系电话要求使用 11 位手机号格式。
mobile_phone_validator = RegexValidator(
    regex=r'^1\d{10}$',
    message='联系电话必须是11位手机号',
)


# 场馆模型：由场馆管理员维护，是场地和时段的上层实体。
class Stadium(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stadiums',
        verbose_name='场馆管理员',
    )
    name = models.CharField('场馆名称', max_length=100)
    address = models.CharField('场馆地址', max_length=255)
    phone_number = models.CharField('联系电话', max_length=20, validators=[mobile_phone_validator])
    information = models.TextField('场馆简介', blank=True)
    cover_image = models.FileField(
        '场馆照片',
        upload_to='stadium_covers/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
    )
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
        # 只有场馆管理员角色的用户才能作为场馆 owner。
        if self.owner_id and self.owner.role != UserRole.STADIUM_ADMIN:
            raise ValidationError('只有场馆管理员可以负责场馆')

    def save(self, *args, **kwargs):
        # 正常保存场馆时统一先跑模型校验。
        self.full_clean()
        return super().save(*args, **kwargs)

    def submit_for_review(self):
        # 提交审核后场馆重新回到待审核，并暂时不对外开放。
        self.audit_status = StadiumAuditStatus.PENDING
        self.is_open = False
        type(self).objects.filter(pk=self.pk).update(
            audit_status=self.audit_status,
            is_open=self.is_open,
        )

    def request_deletion(self):
        # 场馆删除采用“先申请、后审核”的流程，而不是直接物理删除。
        self.deletion_requested = True
        self.audit_status = StadiumAuditStatus.PENDING
        type(self).objects.filter(pk=self.pk).update(
            deletion_requested=self.deletion_requested,
            audit_status=self.audit_status,
        )

    def cancel_deletion_request(self):
        # 撤销删除申请后，场馆恢复到审核通过且开放状态。
        self.deletion_requested = False
        self.audit_status = StadiumAuditStatus.APPROVED
        self.is_open = True
        type(self).objects.filter(pk=self.pk).update(
            deletion_requested=self.deletion_requested,
            audit_status=self.audit_status,
            is_open=self.is_open,
        )

    def approve(self):
        # 如果当前审批的是删除申请，则审核通过后直接删除场馆记录。
        if self.deletion_requested:
            self.delete()
            return 'deleted'

        # 普通审核通过：场馆变为公开开放。
        self.audit_status = StadiumAuditStatus.APPROVED
        self.is_open = True
        type(self).objects.filter(pk=self.pk).update(
            audit_status=self.audit_status,
            is_open=self.is_open,
        )
        return 'approved'

    def reject(self):
        # 拒绝删除申请时恢复场馆；拒绝普通审核时保持不开放。
        if self.deletion_requested:
            self.deletion_requested = False
            self.audit_status = StadiumAuditStatus.APPROVED
            self.is_open = True
        else:
            self.audit_status = StadiumAuditStatus.REJECTED
            self.is_open = False
        type(self).objects.filter(pk=self.pk).update(
            deletion_requested=self.deletion_requested,
            audit_status=self.audit_status,
            is_open=self.is_open,
        )


# 场地模型：隶属于某个场馆，同一场馆下场地编号不能重复。
class Field(models.Model):
    stadium = models.ForeignKey(
        Stadium,
        on_delete=models.CASCADE,
        related_name='fields',
        verbose_name='场馆',
    )
    field_type = models.CharField('场地类型', max_length=50)
    number = models.CharField('场地编号', max_length=50)
    is_active = models.BooleanField('启用状态', default=True)
    price_per_hour = models.DecimalField('预约单价/小时', max_digits=8, decimal_places=2)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['stadium', 'number']
        unique_together = [('stadium', 'number')]
        verbose_name = '场地'
        verbose_name_plural = '场地'

    def __str__(self):
        return f'{self.stadium.name} - {self.number}'

    def clean(self):
        # 只有审核通过的场馆下才允许继续维护场地。
        if self.stadium_id and self.stadium.audit_status != StadiumAuditStatus.APPROVED:
            raise ValidationError('只能在审核通过的场馆下维护场地')

# 时段模型：隶属于某个场地，是预约系统里的最小可预约单元。
class TimeSlot(models.Model):
    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name='场地',
    )
    date = models.DateField('开放日期')
    start_time = models.TimeField('开始时间')
    end_time = models.TimeField('结束时间')
    is_available = models.BooleanField('可约状态', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = '开放时段'
        verbose_name_plural = '开放时段'

    def __str__(self):
        return f'{self.field} {self.date} {self.start_time}-{self.end_time}'

    def clean(self):
        # 起止时间必须形成一个正向区间。
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('开始时间必须早于结束时间')

        # 停用场地不能再新增可预约时段，避免前台继续看到可约数据。
        if self.field_id and self.is_available and not self.field.is_active:
            raise ValidationError('停用场地不能新增可约时段')

        if not all([self.field_id, self.date, self.start_time, self.end_time]):
            return

        # 同一场地同一天的时段不能发生重叠。
        overlapping_slots = TimeSlot.objects.filter(
            field=self.field,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        if self.pk:
            overlapping_slots = overlapping_slots.exclude(pk=self.pk)
        if overlapping_slots.exists():
            raise ValidationError('同一场地同一天的开放时段不能重叠')

    def save(self, *args, **kwargs):
        # 正常保存时段时统一先跑模型校验。
        self.full_clean()
        return super().save(*args, **kwargs)

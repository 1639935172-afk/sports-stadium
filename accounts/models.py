from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    ORDINARY = 'ordinary', _('普通用户')
    STADIUM_ADMIN = 'stadium_admin', _('场馆管理员')
    SYSTEM_ADMIN = 'system_admin', _('系统管理员')


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError('手机号不能为空')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', UserRole.ORDINARY)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.SYSTEM_ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')
        if extra_fields.get('role') != UserRole.SYSTEM_ADMIN:
            raise ValueError('超级用户必须是系统管理员角色')

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None
    phone_number = models.CharField('手机号', max_length=20, unique=True)
    nickname = models.CharField('昵称', max_length=50, blank=True)
    role = models.CharField('角色', max_length=20, choices=UserRole.choices, default=UserRole.ORDINARY)
    is_cancelled = models.BooleanField('已注销', default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.nickname or self.phone_number

    @property
    def is_ordinary_user(self):
        return self.role == UserRole.ORDINARY

    @property
    def is_stadium_admin(self):
        return self.role == UserRole.STADIUM_ADMIN

    @property
    def is_system_admin(self):
        return self.role == UserRole.SYSTEM_ADMIN

    @property
    def can_login(self):
        return self.is_active and not self.is_cancelled

    def cancel_account(self):
        self.is_active = False
        self.is_cancelled = True
        self.save(update_fields=['is_active', 'is_cancelled'])

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import UserRole

DEV_VERIFICATION_CODE = '123456'
DEV_STADIUM_ADMIN_REGISTRATION_CODE = 'STADIUM123'


class RegistrationForm(forms.Form):
    role = forms.ChoiceField(
        label='注册身份',
        required=False,
        initial=UserRole.ORDINARY,
        choices=[
            (UserRole.ORDINARY, '普通用户'),
            (UserRole.STADIUM_ADMIN, '场馆管理员'),
        ],
    )
    phone_number = forms.CharField(label='手机号', max_length=20)
    nickname = forms.CharField(label='昵称', max_length=50, required=False)
    password1 = forms.CharField(label='密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput)
    verification_code = forms.CharField(label='验证码', max_length=6)
    stadium_admin_registration_code = forms.CharField(
        label='场馆管理员注册码',
        max_length=20,
        required=False,
        widget=forms.PasswordInput,
        help_text='注册场馆管理员时必填。',
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()
        if get_user_model().objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('该手机号已注册')
        if not phone_number.isdigit() or len(phone_number) != 11:
            raise forms.ValidationError('手机号必须是11位数字')
        return phone_number

    def clean_password1(self):
        password = self.cleaned_data['password1']
        validate_password(password)
        return password

    def clean_verification_code(self):
        code = self.cleaned_data['verification_code'].strip()
        if code != DEV_VERIFICATION_CODE:
            raise forms.ValidationError('验证码错误')
        return code

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        role = cleaned_data.get('role')
        stadium_admin_registration_code = cleaned_data.get('stadium_admin_registration_code', '').strip()
        if password1 and password2 and password1 != password2:
            self.add_error('password2', '两次输入的密码不一致')
        if role == UserRole.STADIUM_ADMIN and stadium_admin_registration_code != DEV_STADIUM_ADMIN_REGISTRATION_CODE:
            self.add_error('stadium_admin_registration_code', '场馆管理员注册码不正确')
        return cleaned_data

    def save(self):
        return get_user_model().objects.create_user(
            phone_number=self.cleaned_data['phone_number'],
            password=self.cleaned_data['password1'],
            nickname=self.cleaned_data.get('nickname', ''),
            role=self.cleaned_data.get('role', UserRole.ORDINARY),
        )


class LoginForm(forms.Form):
    phone_number = forms.CharField(label='手机号', max_length=20)
    password = forms.CharField(label='密码', widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        password = cleaned_data.get('password')
        if phone_number and password:
            self.user = authenticate(self.request, username=phone_number, password=password)
            if self.user is None or not self.user.can_login:
                raise forms.ValidationError('手机号或密码错误')
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['nickname']
        labels = {'nickname': '昵称'}


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label='当前密码', widget=forms.PasswordInput)
    new_password1 = forms.CharField(label='新密码', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='确认新密码', widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data['old_password']
        if not self.user.check_password(old_password):
            raise forms.ValidationError('当前密码错误')
        return old_password

    def clean_new_password1(self):
        password = self.cleaned_data['new_password1']
        validate_password(password, self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', '两次输入的新密码不一致')
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save(update_fields=['password'])
        return self.user


class PasswordResetForm(forms.Form):
    phone_number = forms.CharField(label='手机号', max_length=20)
    verification_code = forms.CharField(label='验证码', max_length=6)
    new_password1 = forms.CharField(label='新密码', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='确认新密码', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()
        try:
            self.user = get_user_model().objects.get(phone_number=phone_number, is_cancelled=False)
        except get_user_model().DoesNotExist as exc:
            raise forms.ValidationError('该手机号未注册') from exc
        return phone_number

    def clean_verification_code(self):
        code = self.cleaned_data['verification_code'].strip()
        if code != DEV_VERIFICATION_CODE:
            raise forms.ValidationError('验证码错误')
        return code

    def clean_new_password1(self):
        password = self.cleaned_data['new_password1']
        validate_password(password, self.user)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', '两次输入的新密码不一致')
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.is_active = True
        self.user.save(update_fields=['password', 'is_active'])
        return self.user


class AccountCancellationForm(forms.Form):
    password = forms.CharField(label='当前密码', widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise forms.ValidationError('密码不正确')
        return password


class SystemUserManagementForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['nickname', 'role', 'is_active', 'is_cancelled']
        labels = {
            'nickname': '昵称',
            'role': '角色',
            'is_active': '允许登录',
            'is_cancelled': '已注销',
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_cancelled'):
            cleaned_data['is_active'] = False
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.is_cancelled:
            user.is_active = False
        if commit:
            user.save()
        return user

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password


DEV_VERIFICATION_CODE = '123456'


class RegistrationForm(forms.Form):
    phone_number = forms.CharField(label='手机号', max_length=20)
    nickname = forms.CharField(label='昵称', max_length=50, required=False)
    password1 = forms.CharField(label='密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput)
    verification_code = forms.CharField(label='验证码', max_length=6)

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()
        if get_user_model().objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('该手机号已注册')
        if not phone_number.isdigit() or len(phone_number) != 11:
            raise forms.ValidationError('手机号必须是11位数字')
        return phone_number

    def clean_verification_code(self):
        code = self.cleaned_data['verification_code'].strip()
        if code != DEV_VERIFICATION_CODE:
            raise forms.ValidationError('验证码不正确')
        return code

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', '两次输入的密码不一致')
        return cleaned_data

    def save(self):
        return get_user_model().objects.create_user(
            phone_number=self.cleaned_data['phone_number'],
            password=self.cleaned_data['password1'],
            nickname=self.cleaned_data.get('nickname', ''),
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
            self.user = authenticate(
                self.request,
                username=phone_number,
                password=password,
            )
            if self.user is None or not self.user.can_login:
                raise forms.ValidationError('手机号或密码错误')

        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['nickname']
        labels = {'nickname': '昵称'}


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label='原密码', widget=forms.PasswordInput)
    new_password1 = forms.CharField(label='新密码', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='确认新密码', widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data['old_password']
        if not self.user.check_password(old_password):
            raise forms.ValidationError('原密码不正确')
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
            raise forms.ValidationError('验证码不正确')
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

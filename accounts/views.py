from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    DEV_STADIUM_ADMIN_REGISTRATION_CODE,
    DEV_VERIFICATION_CODE,
    AccountCancellationForm,
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    ProfileForm,
    RegistrationForm,
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, '注册成功，已自动登录')
        return redirect('home')

    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
            'dev_verification_code': DEV_VERIFICATION_CODE,
            'dev_stadium_admin_registration_code': DEV_STADIUM_ADMIN_REGISTRATION_CODE,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.user)
        messages.success(request, '登录成功')
        return redirect('home')

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('home')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '个人资料已更新')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def password_change_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, '密码已修改')
        return redirect('accounts:profile')

    return render(request, 'accounts/password_change.html', {'form': form})


def password_reset_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    form = PasswordResetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '密码已重置，请使用新密码登录')
        return redirect('accounts:login')

    return render(
        request,
        'accounts/password_reset.html',
        {'form': form, 'dev_verification_code': DEV_VERIFICATION_CODE},
    )


@login_required
def account_cancel_view(request):
    form = AccountCancellationForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.cancel_account()
        logout(request)
        messages.success(request, '账号已注销')
        return redirect('home')

    return render(request, 'accounts/account_cancel.html', {'form': form})

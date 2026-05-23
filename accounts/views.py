from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserRole
from accounts.permissions import role_required

from .forms import (
    DEV_STADIUM_ADMIN_REGISTRATION_CODE,
    DEV_VERIFICATION_CODE,
    AccountCancellationForm,
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    ProfileForm,
    RegistrationForm,
    SystemUserManagementForm,
)


def _account_template_for(user, ordinary_template, stadium_admin_template, system_admin_template):
    if user.role == UserRole.STADIUM_ADMIN:
        return stadium_admin_template
    if user.role == UserRole.SYSTEM_ADMIN:
        return system_admin_template
    return ordinary_template


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
    template_name = _account_template_for(
        request.user,
        'accounts/profile.html',
        'accounts/stadium_admin_profile.html',
        'accounts/system_admin_profile.html',
    )
    return render(request, template_name)


@login_required
def profile_edit_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '个人资料已更新')
        return redirect('accounts:profile')

    template_name = _account_template_for(
        request.user,
        'accounts/profile_edit.html',
        'accounts/stadium_admin_profile_edit.html',
        'accounts/system_admin_profile_edit.html',
    )
    return render(request, template_name, {'form': form})


@login_required
def password_change_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, '密码已修改')
        return redirect('accounts:profile')

    template_name = _account_template_for(
        request.user,
        'accounts/password_change.html',
        'accounts/stadium_admin_password_change.html',
        'accounts/system_admin_password_change.html',
    )
    return render(request, template_name, {'form': form})


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

    template_name = _account_template_for(
        request.user,
        'accounts/account_cancel.html',
        'accounts/stadium_admin_account_cancel.html',
        'accounts/system_admin_account_cancel.html',
    )
    return render(request, template_name, {'form': form})


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
def system_user_list_view(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    users = get_user_model().objects.all().order_by('phone_number')
    if query:
        users = users.filter(Q(phone_number__icontains=query) | Q(nickname__icontains=query))
    if role in {UserRole.SYSTEM_ADMIN, UserRole.STADIUM_ADMIN, UserRole.ORDINARY}:
        users = users.filter(role=role)
    role_choices = [
        ('', '全部'),
        (UserRole.SYSTEM_ADMIN, '系统管理员'),
        (UserRole.STADIUM_ADMIN, '场馆管理员'),
        (UserRole.ORDINARY, '普通用户'),
    ]
    return render(
        request,
        'accounts/system_user_list.html',
        {'users': users, 'query': query, 'selected_role': role, 'role_choices': role_choices},
    )


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
def system_user_edit_view(request, pk):
    managed_user = get_object_or_404(get_user_model(), pk=pk)
    if managed_user.pk == request.user.pk:
        messages.error(request, '不能在这里管理自己的账号')
        return redirect('accounts:system_user_list')
    if managed_user.role == UserRole.SYSTEM_ADMIN:
        messages.error(request, '系统管理员之间不能互相管理')
        return redirect('accounts:system_user_list')

    form = SystemUserManagementForm(request.POST or None, instance=managed_user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '用户信息已更新')
        return redirect('accounts:system_user_list')

    return render(request, 'accounts/system_user_edit.html', {'form': form, 'managed_user': managed_user})

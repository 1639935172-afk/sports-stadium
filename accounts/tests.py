from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import DEV_VERIFICATION_CODE
from .models import UserRole
from .permissions import is_ordinary_user, is_stadium_admin, is_system_admin


class UserModelTests(TestCase):
    def test_create_user_defaults_to_ordinary_role(self):
        user = get_user_model().objects.create_user(
            phone_number='13800000000',
            password='test-pass',
            nickname='测试用户',
        )

        self.assertEqual(user.role, UserRole.ORDINARY)
        self.assertTrue(user.check_password('test-pass'))
        self.assertTrue(user.can_login)

    def test_create_superuser_is_system_admin(self):
        user = get_user_model().objects.create_superuser(
            phone_number='13900000000',
            password='admin-pass',
        )

        self.assertEqual(user.role, UserRole.SYSTEM_ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_cancel_account_disables_login(self):
        user = get_user_model().objects.create_user(
            phone_number='13700000000',
            password='test-pass',
        )

        user.cancel_account()

        self.assertFalse(user.is_active)
        self.assertTrue(user.is_cancelled)
        self.assertFalse(user.can_login)


class PermissionTests(TestCase):
    def test_role_helpers_require_matching_active_user(self):
        User = get_user_model()
        ordinary = User.objects.create_user(phone_number='13600000000', password='pass')
        stadium_admin = User.objects.create_user(
            phone_number='13500000000',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        system_admin = User.objects.create_user(
            phone_number='13400000000',
            password='pass',
            role=UserRole.SYSTEM_ADMIN,
        )

        self.assertTrue(is_ordinary_user(ordinary))
        self.assertTrue(is_stadium_admin(stadium_admin))
        self.assertTrue(is_system_admin(system_admin))
        self.assertFalse(is_system_admin(ordinary))

    def test_cancelled_user_has_no_role_permission(self):
        user = get_user_model().objects.create_user(phone_number='13300000000', password='pass')
        user.cancel_account()

        self.assertFalse(is_ordinary_user(user))


class AuthFlowTests(TestCase):
    def test_register_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'phone_number': '13200000000',
                'nickname': '新用户',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'verification_code': DEV_VERIFICATION_CODE,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))
        user = get_user_model().objects.get(phone_number='13200000000')
        self.assertEqual(user.nickname, '新用户')
        self.assertEqual(str(self.client.session['_auth_user_id']), str(user.pk))

    def test_register_rejects_duplicate_phone_number(self):
        get_user_model().objects.create_user(phone_number='13200000001', password='pass')

        response = self.client.post(
            reverse('accounts:register'),
            {
                'phone_number': '13200000001',
                'nickname': '重复用户',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'verification_code': DEV_VERIFICATION_CODE,
            },
        )

        self.assertContains(response, '该手机号已注册')

    def test_register_rejects_wrong_verification_code(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'phone_number': '13200000002',
                'nickname': '验证码错误',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'verification_code': '000000',
            },
        )

        self.assertContains(response, '验证码不正确')
        self.assertFalse(get_user_model().objects.filter(phone_number='13200000002').exists())

    def test_register_rejects_phone_number_that_is_not_11_digits(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'phone_number': '132000',
                'nickname': '短手机号',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'verification_code': DEV_VERIFICATION_CODE,
            },
        )

        self.assertContains(response, '手机号必须是11位数字')
        self.assertFalse(get_user_model().objects.filter(phone_number='132000').exists())

    def test_login_accepts_valid_credentials(self):
        user = get_user_model().objects.create_user(
            phone_number='13200000003',
            password='StrongPass123',
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'phone_number': '13200000003', 'password': 'StrongPass123'},
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(str(self.client.session['_auth_user_id']), str(user.pk))

    def test_login_rejects_invalid_credentials(self):
        get_user_model().objects.create_user(phone_number='13200000004', password='StrongPass123')

        response = self.client.post(
            reverse('accounts:login'),
            {'phone_number': '13200000004', 'password': 'wrong-pass'},
        )

        self.assertContains(response, '手机号或密码错误')
        self.assertNotIn('_auth_user_id', self.client.session)


class AccountManagementFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            phone_number='13100000000',
            password='OldPass123',
            nickname='旧昵称',
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_user_can_view_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:profile'))

        self.assertContains(response, '13100000000')
        self.assertContains(response, '旧昵称')

    def test_user_can_update_nickname(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:profile_edit'),
            {'nickname': '新昵称'},
            follow=True,
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, '新昵称')

    def test_user_can_change_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:password_change'),
            {
                'old_password': 'OldPass123',
                'new_password1': 'NewPass123',
                'new_password2': 'NewPass123',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_password_change_rejects_wrong_old_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:password_change'),
            {
                'old_password': 'WrongPass123',
                'new_password1': 'NewPass123',
                'new_password2': 'NewPass123',
            },
        )

        self.assertContains(response, '原密码不正确')

    def test_password_reset_updates_password(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {
                'phone_number': '13100000000',
                'verification_code': DEV_VERIFICATION_CODE,
                'new_password1': 'ResetPass123',
                'new_password2': 'ResetPass123',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('accounts:login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ResetPass123'))

    def test_password_reset_rejects_wrong_verification_code(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {
                'phone_number': '13100000000',
                'verification_code': '000000',
                'new_password1': 'ResetPass123',
                'new_password2': 'ResetPass123',
            },
        )

        self.assertContains(response, '验证码不正确')

    def test_user_can_cancel_account(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:account_cancel'),
            {'password': 'OldPass123'},
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_cancelled)
        self.assertFalse(self.user.is_active)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cancel_account_rejects_wrong_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('accounts:account_cancel'),
            {'password': 'WrongPass123'},
        )

        self.assertContains(response, '密码不正确')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_cancelled)

    def test_logout_clears_session(self):
        user = get_user_model().objects.create_user(
            phone_number='13200000005',
            password='StrongPass123',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:logout'), follow=True)

        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

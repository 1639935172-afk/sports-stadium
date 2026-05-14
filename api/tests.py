from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserRole
from comments.models import Comment, CommentAuditStatus
from reservations.models import Reservation, ReservationStatus
from stadiums.models import Field, Stadium, StadiumAuditStatus, TimeSlot


class ApiBaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()
        self.stadium_admin = self.User.objects.create_user(
            phone_number='18800000001',
            password='DemoPass123',
            nickname='Stadium Admin',
            role=UserRole.STADIUM_ADMIN,
        )
        self.user = self.User.objects.create_user(
            phone_number='18800000002',
            password='DemoPass123',
            nickname='Ordinary User',
            role=UserRole.ORDINARY,
        )
        self.other_user = self.User.objects.create_user(
            phone_number='18800000003',
            password='DemoPass123',
            nickname='Other User',
            role=UserRole.ORDINARY,
        )
        self.stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='API Stadium',
            address='API Road',
            phone_number='13900000000',
            information='API test stadium',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        self.field = Field.objects.create(
            stadium=self.stadium,
            field_type='篮球',
            number='A1',
            price_per_hour='80.00',
        )
        self.time_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2030, 1, 1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_available=True,
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)


class AuthApiTests(ApiBaseTestCase):
    def test_register_creates_ordinary_user(self):
        response = self.client.post(reverse('api:register'), {
            'phone_number': '18800000009',
            'nickname': 'New User',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
            'verification_code': '123456',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = self.User.objects.get(phone_number='18800000009')
        self.assertEqual(user.role, UserRole.ORDINARY)
        self.assertIn('user', response.data)

    def test_register_rejects_weak_password(self):
        response = self.client.post(reverse('api:register'), {
            'phone_number': '18800000010',
            'password1': '123456',
            'password2': '123456',
            'verification_code': '123456',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_jwt_and_user(self):
        response = self.client.post(reverse('api:login'), {
            'phone_number': self.user.phone_number,
            'password': 'DemoPass123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['phone_number'], self.user.phone_number)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('api:profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.authenticate()
        response = self.client.get(reverse('api:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.user.phone_number)

    def test_user_can_update_profile(self):
        self.authenticate()
        response = self.client.patch(reverse('api:profile'), {'nickname': 'Updated'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, 'Updated')
        self.assertEqual(response.data['nickname'], 'Updated')

    def test_user_can_change_password(self):
        self.authenticate()
        response = self.client.post(reverse('api:password_change'), {
            'old_password': 'DemoPass123',
            'new_password1': 'NewDemoPass123',
            'new_password2': 'NewDemoPass123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewDemoPass123'))

    def test_user_can_reset_password_with_verification_code(self):
        response = self.client.post(reverse('api:password_reset'), {
            'phone_number': self.user.phone_number,
            'verification_code': '123456',
            'new_password1': 'ResetDemoPass123',
            'new_password2': 'ResetDemoPass123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ResetDemoPass123'))

    def test_user_can_cancel_account(self):
        self.authenticate()
        response = self.client.post(reverse('api:account_cancel'), {'password': 'DemoPass123'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_cancelled)
        self.assertFalse(self.user.is_active)


class StadiumApiTests(ApiBaseTestCase):
    def test_public_stadium_list_only_returns_approved_open_stadiums(self):
        Stadium.objects.create(
            owner=self.stadium_admin,
            name='Hidden Stadium',
            address='Hidden Road',
            phone_number='13900000001',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )

        response = self.client.get(reverse('api:stadium_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data]
        self.assertEqual(names, ['API Stadium'])

    def test_stadium_detail_hides_occupied_time_slots(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)

        response = self.client.get(reverse('api:stadium_detail', args=[self.stadium.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fields'][0]['time_slots'], [])

    def test_stadium_comments_only_return_approved_comments(self):
        Comment.objects.create(user=self.user, stadium=self.stadium, content='approved', audit_status=CommentAuditStatus.APPROVED)
        Comment.objects.create(user=self.other_user, stadium=self.stadium, content='pending', audit_status=CommentAuditStatus.PENDING)

        response = self.client.get(reverse('api:stadium_comments', args=[self.stadium.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'approved')


class ReservationApiTests(ApiBaseTestCase):
    def test_unauthenticated_user_cannot_create_reservation(self):
        response = self.client.post(reverse('api:reservation_create'), {'time_slot': self.time_slot.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordinary_user_can_create_reservation(self):
        self.authenticate()
        response = self.client.post(reverse('api:reservation_create'), {'time_slot': self.time_slot.pk}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reservation = Reservation.objects.get(user=self.user)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_duplicate_occupied_time_slot_is_rejected(self):
        Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)
        self.authenticate()

        response = self.client.post(reverse('api:reservation_create'), {'time_slot': self.time_slot.pk}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_user_can_list_own_reservations(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.authenticate()

        response = self.client.get(reverse('api:my_reservations'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['stadium_name'], self.stadium.name)

    def test_user_can_cancel_own_reservation(self):
        reservation = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.authenticate()

        response = self.client.post(reverse('api:reservation_cancel', args=[reservation.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_user_cannot_cancel_other_users_reservation(self):
        reservation = Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)
        self.authenticate()

        response = self.client.post(reverse('api:reservation_cancel', args=[reservation.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CommentApiTests(ApiBaseTestCase):
    def test_unauthenticated_user_cannot_create_comment(self):
        response = self.client.post(reverse('api:comment_create'), {
            'stadium': self.stadium.pk,
            'content': 'Good',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordinary_user_can_create_pending_comment(self):
        self.authenticate()
        response = self.client.post(reverse('api:comment_create'), {
            'stadium': self.stadium.pk,
            'content': 'Good',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(user=self.user)
        self.assertEqual(comment.audit_status, CommentAuditStatus.PENDING)

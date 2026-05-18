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
        self.system_admin = self.User.objects.create_user(
            phone_number='18800000000',
            password='DemoPass123',
            nickname='System Admin',
            role=UserRole.SYSTEM_ADMIN,
            is_staff=True,
        )
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

    def test_system_admin_can_list_users(self):
        self.authenticate(self.system_admin)

        response = self.client.get(reverse('api:system_user_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

    def test_system_admin_can_search_users(self):
        self.authenticate(self.system_admin)

        response = self.client.get(reverse('api:system_user_list'), {'q': self.user.phone_number})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['phone_number'], self.user.phone_number)

    def test_system_admin_can_update_other_user(self):
        self.authenticate(self.system_admin)

        response = self.client.patch(reverse('api:system_user_detail', args=[self.user.pk]), {
            'nickname': 'Managed User',
            'role': UserRole.STADIUM_ADMIN,
            'is_active': True,
            'is_cancelled': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, 'Managed User')
        self.assertEqual(self.user.role, UserRole.STADIUM_ADMIN)

    def test_system_admin_cannot_manage_self(self):
        self.authenticate(self.system_admin)

        response = self.client.patch(reverse('api:system_user_detail', args=[self.system_admin.pk]), {
            'nickname': 'Self Edit',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_system_admin_cannot_access_system_user_api(self):
        self.authenticate(self.user)

        response = self.client.get(reverse('api:system_user_list'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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

    def test_stadium_admin_can_list_own_stadiums(self):
        Stadium.objects.create(
            owner=self.stadium_admin,
            name='Second Stadium',
            address='Second Road',
            phone_number='13900000066',
            information='Managed by same admin',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )
        self.authenticate(self.stadium_admin)

        response = self.client.get(reverse('api:stadium_mine'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_stadium_admin_can_create_stadium(self):
        self.authenticate(self.stadium_admin)

        response = self.client.post(reverse('api:stadium_mine'), {
            'name': 'New Stadium',
            'address': 'Create Road',
            'phone_number': '13900000055',
            'information': 'Created from API',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stadium = Stadium.objects.get(name='New Stadium')
        self.assertEqual(stadium.owner, self.stadium_admin)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.PENDING)
        self.assertFalse(stadium.is_open)

    def test_stadium_admin_cannot_create_stadium_with_invalid_phone_number(self):
        self.authenticate(self.stadium_admin)

        response = self.client.post(reverse('api:stadium_mine'), {
            'name': 'Bad Phone Stadium',
            'address': 'Create Road',
            'phone_number': '02512345678',
            'information': 'Created from API',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
        self.assertFalse(Stadium.objects.filter(name='Bad Phone Stadium').exists())

    def test_stadium_admin_can_edit_own_stadium_and_resubmit(self):
        self.stadium.audit_status = StadiumAuditStatus.APPROVED
        self.stadium.is_open = True
        self.stadium.save(update_fields=['audit_status', 'is_open'])
        self.authenticate(self.stadium_admin)

        response = self.client.patch(reverse('api:stadium_mine_detail', args=[self.stadium.pk]), {
            'name': 'Updated Stadium',
            'information': 'Updated info',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.stadium.refresh_from_db()
        self.assertEqual(self.stadium.name, 'Updated Stadium')
        self.assertEqual(self.stadium.audit_status, StadiumAuditStatus.PENDING)
        self.assertFalse(self.stadium.is_open)
        self.assertFalse(self.stadium.deletion_requested)

    def test_stadium_admin_can_request_deletion(self):
        self.stadium.audit_status = StadiumAuditStatus.APPROVED
        self.stadium.is_open = True
        self.stadium.save(update_fields=['audit_status', 'is_open'])
        self.authenticate(self.stadium_admin)

        response = self.client.post(reverse('api:stadium_mine_delete_request', args=[self.stadium.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.stadium.refresh_from_db()
        self.assertTrue(self.stadium.deletion_requested)
        self.assertEqual(self.stadium.audit_status, StadiumAuditStatus.PENDING)

    def test_stadium_admin_can_request_deletion_for_legacy_invalid_phone_number(self):
        Stadium.objects.filter(pk=self.stadium.pk).update(
            phone_number='198',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        self.authenticate(self.stadium_admin)

        response = self.client.post(
            reverse('api:stadium_mine_delete_request', args=[self.stadium.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.stadium.refresh_from_db()
        self.assertTrue(self.stadium.deletion_requested)
        self.assertEqual(self.stadium.audit_status, StadiumAuditStatus.PENDING)

    def test_non_stadium_admin_cannot_manage_stadiums(self):
        self.authenticate(self.user)

        response = self.client.get(reverse('api:stadium_mine'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_system_admin_can_list_pending_stadiums(self):
        pending = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Pending Stadium',
            address='Pending Road',
            phone_number='13900000088',
            information='Waiting for review',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )
        self.authenticate(self.system_admin)

        response = self.client.get(reverse('api:stadium_admin_pending'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], pending.pk)
        self.assertEqual(response.data[0]['owner_phone_number'], self.stadium_admin.phone_number)

    def test_system_admin_can_approve_pending_stadium(self):
        pending = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Pending Stadium',
            address='Pending Road',
            phone_number='13900000088',
            information='Waiting for review',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )
        self.authenticate(self.system_admin)

        response = self.client.post(reverse('api:stadium_admin_approve', args=[pending.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending.refresh_from_db()
        self.assertEqual(pending.audit_status, StadiumAuditStatus.APPROVED)
        self.assertTrue(pending.is_open)

    def test_system_admin_can_approve_stadium_deletion_request(self):
        stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Deleting Stadium',
            address='Deleting Road',
            phone_number='13900000076',
            information='Delete me',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
            deletion_requested=True,
        )
        self.authenticate(self.system_admin)

        response = self.client.post(reverse('api:stadium_admin_approve', args=[stadium.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'deleted')
        self.assertFalse(Stadium.objects.filter(pk=stadium.pk).exists())

    def test_system_admin_can_reject_stadium_deletion_request(self):
        stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Deleting Stadium',
            address='Deleting Road',
            phone_number='13900000077',
            information='Delete me',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
            deletion_requested=True,
        )
        stadium.audit_status = StadiumAuditStatus.PENDING
        stadium.is_open = False
        stadium.save(update_fields=['audit_status', 'is_open', 'deletion_requested'])
        self.authenticate(self.system_admin)

        response = self.client.post(reverse('api:stadium_admin_reject', args=[stadium.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stadium.refresh_from_db()
        self.assertFalse(stadium.deletion_requested)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.APPROVED)
        self.assertTrue(stadium.is_open)

    def test_non_system_admin_cannot_access_stadium_audit_api(self):
        self.authenticate(self.user)

        response = self.client.get(reverse('api:stadium_admin_pending'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stadium_admin_can_list_fields_for_own_approved_stadium(self):
        field = Field.objects.create(
            stadium=self.stadium,
            field_type='羽毛球',
            number='B1',
            price_per_hour='60.00',
        )
        self.authenticate(self.stadium_admin)

        response = self.client.get(
            reverse('api:field_manage_list_create', args=[self.stadium.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        numbers = {item['number'] for item in response.data}
        self.assertIn(field.number, numbers)

    def test_stadium_admin_can_create_update_disable_and_delete_field(self):
        self.authenticate(self.stadium_admin)

        create_response = self.client.post(
            reverse('api:field_manage_list_create', args=[self.stadium.pk]),
            {
                'field_type': '网球',
                'number': 'C1',
                'is_active': True,
                'price_per_hour': '100.00',
            },
            format='json',
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        field = Field.objects.get(stadium=self.stadium, number='C1')

        update_response = self.client.patch(
            reverse('api:field_manage_detail', args=[field.pk]),
            {'field_type': '室内网球', 'price_per_hour': '120.00'},
            format='json',
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        field.refresh_from_db()
        self.assertEqual(field.field_type, '室内网球')
        self.assertEqual(str(field.price_per_hour), '120.00')

        disable_response = self.client.post(
            reverse('api:field_disable', args=[field.pk]),
        )

        self.assertEqual(disable_response.status_code, status.HTTP_200_OK)
        field.refresh_from_db()
        self.assertFalse(field.is_active)

        delete_response = self.client.delete(
            reverse('api:field_manage_detail', args=[field.pk]),
        )

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Field.objects.filter(pk=field.pk).exists())

    def test_stadium_admin_cannot_manage_fields_for_unapproved_stadium(self):
        pending_stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Pending Stadium',
            address='Pending Road',
            phone_number='13900000091',
            information='Waiting',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )
        self.authenticate(self.stadium_admin)

        response = self.client.get(
            reverse('api:field_manage_list_create', args=[pending_stadium.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stadium_admin_can_list_create_update_and_delete_time_slots(self):
        self.authenticate(self.stadium_admin)

        list_response = self.client.get(
            reverse('api:time_slot_manage_list_create', args=[self.field.pk]),
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

        create_response = self.client.post(
            reverse('api:time_slot_manage_list_create', args=[self.field.pk]),
            {
                'date': '2030-01-02',
                'start_time': '10:00:00',
                'end_time': '11:00:00',
                'is_available': True,
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        slot = TimeSlot.objects.get(field=self.field, date='2030-01-02')

        update_response = self.client.patch(
            reverse('api:time_slot_manage_detail', args=[slot.pk]),
            {'start_time': '11:00:00', 'end_time': '12:00:00'},
            format='json',
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        slot.refresh_from_db()
        self.assertEqual(str(slot.start_time), '11:00:00')

        delete_response = self.client.delete(
            reverse('api:time_slot_manage_detail', args=[slot.pk]),
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TimeSlot.objects.filter(pk=slot.pk).exists())

    def test_time_slot_conflict_returns_validation_error(self):
        self.authenticate(self.stadium_admin)

        response = self.client.post(
            reverse('api:time_slot_manage_list_create', args=[self.field.pk]),
            {
                'date': '2030-01-01',
                'start_time': '09:30:00',
                'end_time': '10:30:00',
                'is_available': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_time_slot_for_inactive_field(self):
        self.field.is_active = False
        self.field.save(update_fields=['is_active'])
        self.authenticate(self.stadium_admin)

        response = self.client.post(
            reverse('api:time_slot_manage_list_create', args=[self.field.pk]),
            {
                'date': '2030-01-02',
                'start_time': '10:00:00',
                'end_time': '11:00:00',
                'is_available': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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

    def test_stadium_admin_can_list_pending_reservations_for_own_stadium(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.authenticate(self.stadium_admin)

        response = self.client.get(reverse('api:admin_pending_reservations'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['stadium_name'], self.stadium.name)

    def test_stadium_admin_can_approve_pending_reservation(self):
        reservation = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.authenticate(self.stadium_admin)

        response = self.client.post(reverse('api:reservation_approve', args=[reservation.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.APPROVED)

    def test_stadium_admin_can_reject_pending_reservation(self):
        reservation = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.authenticate(self.stadium_admin)

        response = self.client.post(reverse('api:reservation_reject', args=[reservation.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.REJECTED)


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

    def test_ordinary_user_can_list_own_comments(self):
        mine = Comment.objects.create(
            user=self.user,
            stadium=self.stadium,
            content='my comment',
            audit_status=CommentAuditStatus.PENDING,
        )
        Comment.objects.create(
            user=self.other_user,
            stadium=self.stadium,
            content='other comment',
            audit_status=CommentAuditStatus.APPROVED,
        )
        self.authenticate()

        response = self.client.get(reverse('api:my_comments'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], mine.pk)
        self.assertEqual(response.data[0]['content'], 'my comment')

    def test_ordinary_user_can_delete_own_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            stadium=self.stadium,
            content='delete me',
            audit_status=CommentAuditStatus.PENDING,
        )
        self.authenticate()

        response = self.client.delete(reverse('api:my_comment_delete', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_ordinary_user_cannot_delete_other_users_comment(self):
        comment = Comment.objects.create(
            user=self.other_user,
            stadium=self.stadium,
            content='not yours',
            audit_status=CommentAuditStatus.PENDING,
        )
        self.authenticate()

        response = self.client.delete(reverse('api:my_comment_delete', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_system_admin_can_list_pending_comments(self):
        Comment.objects.create(
            user=self.user,
            stadium=self.stadium,
            content='pending',
            audit_status=CommentAuditStatus.PENDING,
        )
        self.authenticate(self.system_admin)

        response = self.client.get(reverse('api:comment_admin_pending'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'pending')

    def test_system_admin_can_approve_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            stadium=self.stadium,
            content='pending',
            audit_status=CommentAuditStatus.PENDING,
        )
        self.authenticate(self.system_admin)

        response = self.client.post(reverse('api:comment_admin_approve', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.audit_status, CommentAuditStatus.APPROVED)

    def test_system_admin_can_reject_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            stadium=self.stadium,
            content='pending',
            audit_status=CommentAuditStatus.PENDING,
        )
        self.authenticate(self.system_admin)

        response = self.client.post(reverse('api:comment_admin_reject', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.audit_status, CommentAuditStatus.REJECTED)

    def test_system_admin_can_delete_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            stadium=self.stadium,
            content='pending',
            audit_status=CommentAuditStatus.PENDING,
        )
        self.authenticate(self.system_admin)

        response = self.client.delete(reverse('api:comment_admin_delete', args=[comment.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

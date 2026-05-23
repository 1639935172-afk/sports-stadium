from datetime import date, time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole

from .models import Field, Stadium, StadiumAuditStatus, TimeSlot


TEST_MEDIA_ROOT = Path(__file__).resolve().parent.parent / 'test_media'


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class StadiumWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.stadium_admin = User.objects.create_user(
            phone_number='13000000001',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
            nickname='场馆管理员',
        )
        self.other_stadium_admin = User.objects.create_user(
            phone_number='13000000002',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.system_admin = User.objects.create_user(
            phone_number='13000000003',
            password='pass',
            role=UserRole.SYSTEM_ADMIN,
        )
        self.ordinary_user = User.objects.create_user(
            phone_number='13000000004',
            password='pass',
            role=UserRole.ORDINARY,
        )

    def tearDown(self):
        if TEST_MEDIA_ROOT.exists():
            for path in sorted(TEST_MEDIA_ROOT.rglob('*'), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()

    def stadium_payload(self, **overrides):
        payload = {
            'name': '南航体育馆',
            'address': '南京市江宁区将军大道',
            'phone_number': '13812345678',
            'information': '综合体育场馆',
        }
        payload.update(overrides)
        return payload

    def image_upload(self, name='stadium.jpg'):
        return SimpleUploadedFile(
            name,
            (
                b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
                b'\xff\xdb\x00C\x00' + b'\x08' * 64 +
                b'\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01'
                b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08'
                b'\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9'
            ),
            content_type='image/jpeg',
        )

    def create_pending_stadium(self, owner=None):
        return Stadium.objects.create(
            owner=owner or self.stadium_admin,
            **self.stadium_payload(),
        )

    def test_stadium_admin_can_submit_stadium_for_review(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:create'),
            self.stadium_payload(cover_image=self.image_upload()),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:my_stadiums'))
        stadium = Stadium.objects.get(name='南航体育馆')
        self.assertEqual(stadium.owner, self.stadium_admin)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.PENDING)
        self.assertFalse(stadium.is_open)
        self.assertTrue(stadium.cover_image.name.startswith('stadium_covers/'))

    def test_stadium_phone_number_must_be_eleven_digit_mobile(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:create'),
            self.stadium_payload(phone_number='12345'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '联系电话必须是11位手机号')
        self.assertFalse(Stadium.objects.exists())

    def test_ordinary_user_cannot_submit_stadium(self):
        self.client.force_login(self.ordinary_user)

        response = self.client.post(reverse('stadiums:create'), self.stadium_payload())

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Stadium.objects.exists())

    def test_system_admin_can_approve_pending_stadium(self):
        stadium = self.create_pending_stadium()
        self.client.force_login(self.system_admin)

        response = self.client.post(reverse('stadiums:audit_approve', args=[stadium.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:audit_list'))
        stadium.refresh_from_db()
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.APPROVED)
        self.assertTrue(stadium.is_open)

    def test_system_admin_can_reject_pending_stadium(self):
        stadium = self.create_pending_stadium()
        self.client.force_login(self.system_admin)

        response = self.client.post(reverse('stadiums:audit_reject', args=[stadium.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:audit_list'))
        stadium.refresh_from_db()
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.REJECTED)
        self.assertFalse(stadium.is_open)

    def test_non_system_admin_cannot_access_audit_list(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.get(reverse('stadiums:audit_list'))

        self.assertEqual(response.status_code, 403)

    def test_stadium_admin_can_edit_own_stadium_and_resubmit(self):
        stadium = self.create_pending_stadium()
        stadium.approve()
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:edit', args=[stadium.pk]),
            self.stadium_payload(name='更新后的体育馆'),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:my_stadiums'))
        stadium.refresh_from_db()
        self.assertEqual(stadium.name, '更新后的体育馆')
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.PENDING)
        self.assertFalse(stadium.is_open)

    def test_stadium_admin_cannot_edit_other_owner_stadium(self):
        stadium = self.create_pending_stadium(owner=self.other_stadium_admin)
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:edit', args=[stadium.pk]),
            self.stadium_payload(name='非法修改'),
        )

        self.assertEqual(response.status_code, 404)
        stadium.refresh_from_db()
        self.assertNotEqual(stadium.name, '非法修改')

    def test_stadium_admin_can_request_deletion_and_system_admin_can_approve(self):
        stadium = self.create_pending_stadium()
        stadium.approve()
        self.client.force_login(self.stadium_admin)

        response = self.client.post(reverse('stadiums:delete_request', args=[stadium.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:my_stadiums'))
        stadium.refresh_from_db()
        self.assertTrue(stadium.deletion_requested)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.PENDING)

        self.client.force_login(self.system_admin)
        response = self.client.post(reverse('stadiums:audit_approve', args=[stadium.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:audit_list'))
        self.assertFalse(Stadium.objects.filter(pk=stadium.pk).exists())

    def test_can_request_deletion_for_legacy_stadium_with_invalid_phone_number(self):
        stadium = self.create_pending_stadium()
        Stadium.objects.filter(pk=stadium.pk).update(
            phone_number='198',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        stadium.refresh_from_db()
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:delete_request', args=[stadium.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:my_stadiums'))
        stadium.refresh_from_db()
        self.assertTrue(stadium.deletion_requested)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.PENDING)

    def test_rejecting_deletion_request_keeps_approved_stadium(self):
        stadium = self.create_pending_stadium()
        stadium.approve()
        stadium.request_deletion()
        self.client.force_login(self.system_admin)

        response = self.client.post(reverse('stadiums:audit_reject', args=[stadium.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:audit_list'))
        stadium.refresh_from_db()
        self.assertFalse(stadium.deletion_requested)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.APPROVED)
        self.assertTrue(stadium.is_open)

    def test_stadium_admin_can_cancel_own_deletion_request(self):
        stadium = self.create_pending_stadium()
        stadium.approve()
        stadium.request_deletion()
        self.client.force_login(self.stadium_admin)

        response = self.client.post(reverse('stadiums:delete_request_cancel', args=[stadium.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:my_stadiums'))
        stadium.refresh_from_db()
        self.assertFalse(stadium.deletion_requested)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.APPROVED)
        self.assertTrue(stadium.is_open)

    def test_stadium_admin_can_open_user_view_preview_modal_for_own_stadium(self):
        stadium = self.create_pending_stadium()
        stadium.approve()
        Field.objects.create(
            stadium=stadium,
            number='A1',
            field_type='羽毛球',
            price_per_hour='88.00',
            is_active=True,
        )
        self.client.force_login(self.stadium_admin)

        response = self.client.get(reverse('stadiums:my_stadiums'), {'modal': 'preview', 'preview': stadium.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '用户视角详情预览')
        self.assertContains(response, stadium.name)
        self.assertContains(response, 'A1')

    def test_stadium_admin_can_update_cover_image_from_preview_modal(self):
        stadium = self.create_pending_stadium()
        stadium.approve()
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:cover_update', args=[stadium.pk]),
            {'cover_image': self.image_upload('preview.jpg')},
            follow=True,
        )

        self.assertRedirects(response, f"{reverse('stadiums:my_stadiums')}?modal=preview&preview={stadium.pk}")
        stadium.refresh_from_db()
        self.assertTrue(stadium.cover_image.name.startswith('stadium_covers/'))
        self.assertContains(response, '场馆照片已更新')

    def test_detail_page_shows_uploaded_cover_image(self):
        stadium = self.create_stadium_with_image()

        response = self.client.get(reverse('stadiums:detail', args=[stadium.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, stadium.cover_image.url)

    def create_stadium_with_image(self):
        stadium = self.create_pending_stadium()
        stadium.cover_image = self.image_upload()
        stadium.save()
        stadium.approve()
        stadium.refresh_from_db()
        return stadium


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PublicStadiumTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.stadium_admin = User.objects.create_user(
            phone_number='13100000001',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.ordinary_user = User.objects.create_user(
            phone_number='13100000002',
            password='pass',
            role=UserRole.ORDINARY,
        )

    def tearDown(self):
        if TEST_MEDIA_ROOT.exists():
            for path in sorted(TEST_MEDIA_ROOT.rglob('*'), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()

    def create_stadium(self, name, **overrides):
        data = {
            'owner': self.stadium_admin,
            'name': name,
            'address': f'{name} address',
            'phone_number': '13812345678',
            'information': f'{name} information',
            'audit_status': StadiumAuditStatus.APPROVED,
            'is_open': True,
            'deletion_requested': False,
        }
        data.update(overrides)
        return Stadium.objects.create(**data)

    def test_public_list_shows_only_approved_open_stadiums(self):
        visible = self.create_stadium('Visible Center')
        pending = self.create_stadium('Pending Center', audit_status=StadiumAuditStatus.PENDING, is_open=False)
        rejected = self.create_stadium('Rejected Center', audit_status=StadiumAuditStatus.REJECTED, is_open=False)
        closed = self.create_stadium('Closed Center', is_open=False)
        deletion_requested = self.create_stadium('Deleting Center', deletion_requested=True)

        response = self.client.get(reverse('stadiums:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.name)
        self.assertNotContains(response, pending.name)
        self.assertNotContains(response, rejected.name)
        self.assertNotContains(response, closed.name)
        self.assertNotContains(response, deletion_requested.name)

    def test_public_list_can_search_by_name(self):
        self.create_stadium('North Basketball Arena')
        self.create_stadium('South Tennis Hall')

        response = self.client.get(reverse('stadiums:list'), {'q': 'Basketball'})

        self.assertContains(response, 'North Basketball Arena')
        self.assertNotContains(response, 'South Tennis Hall')

    def test_public_list_can_search_by_active_field_type_or_number(self):
        north = self.create_stadium('North Sports Center')
        south = self.create_stadium('South Sports Center')
        Field.objects.create(
            stadium=north,
            field_type='羽毛球',
            number='A12',
            price_per_hour='80.00',
            is_active=True,
        )
        Field.objects.create(
            stadium=south,
            field_type='篮球',
            number='B08',
            price_per_hour='90.00',
            is_active=True,
        )
        Field.objects.create(
            stadium=south,
            field_type='网球',
            number='X99',
            price_per_hour='100.00',
            is_active=False,
        )

        type_response = self.client.get(reverse('stadiums:list'), {'q': '羽毛球'})
        self.assertContains(type_response, north.name)
        self.assertNotContains(type_response, south.name)

        number_response = self.client.get(reverse('stadiums:list'), {'q': 'B08'})
        self.assertContains(number_response, south.name)
        self.assertNotContains(number_response, north.name)

        inactive_response = self.client.get(reverse('stadiums:list'), {'q': 'X99'})
        self.assertNotContains(inactive_response, south.name)

    def test_public_detail_allows_public_stadium(self):
        stadium = self.create_stadium('Public Detail Center')

        response = self.client.get(reverse('stadiums:detail', args=[stadium.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, stadium.name)
        self.assertContains(response, stadium.address)
        self.assertContains(response, stadium.phone_number)

    def test_public_detail_returns_404_for_non_public_stadium(self):
        pending = self.create_stadium(
            'Hidden Pending Center',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )

        response = self.client.get(reverse('stadiums:detail', args=[pending.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anonymous_and_ordinary_users_can_access_public_pages(self):
        stadium = self.create_stadium('Everyone Center')

        list_response = self.client.get(reverse('stadiums:list'))
        detail_response = self.client.get(reverse('stadiums:detail', args=[stadium.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)


class FieldManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.stadium_admin = User.objects.create_user(
            phone_number='13200000001',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.other_stadium_admin = User.objects.create_user(
            phone_number='13200000002',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.ordinary_user = User.objects.create_user(
            phone_number='13200000003',
            password='pass',
            role=UserRole.ORDINARY,
        )
        self.approved_stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Approved Stadium',
            address='Address',
            phone_number='13812345678',
            information='Info',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        self.pending_stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Pending Stadium',
            address='Address',
            phone_number='13812345679',
            information='Info',
        )
        self.other_stadium = Stadium.objects.create(
            owner=self.other_stadium_admin,
            name='Other Stadium',
            address='Address',
            phone_number='13812345680',
            information='Info',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )

    def field_payload(self, **overrides):
        payload = {
            'field_type': 'Basketball',
            'number': 'A1',
            'is_active': 'on',
            'price_per_hour': '80.00',
        }
        payload.update(overrides)
        return payload

    def test_stadium_admin_can_create_field_under_own_approved_stadium(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:field_create', args=[self.approved_stadium.pk]),
            self.field_payload(),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:field_list', args=[self.approved_stadium.pk]))
        field = Field.objects.get(stadium=self.approved_stadium)
        self.assertEqual(field.number, 'A1')
        self.assertEqual(field.field_type, 'Basketball')
        self.assertTrue(field.is_active)

    def test_cannot_create_field_under_unapproved_or_other_stadium(self):
        self.client.force_login(self.stadium_admin)

        pending_response = self.client.post(
            reverse('stadiums:field_create', args=[self.pending_stadium.pk]),
            self.field_payload(number='P1'),
        )
        other_response = self.client.post(
            reverse('stadiums:field_create', args=[self.other_stadium.pk]),
            self.field_payload(number='O1'),
        )

        self.assertEqual(pending_response.status_code, 404)
        self.assertEqual(other_response.status_code, 404)
        self.assertFalse(Field.objects.exists())

    def test_ordinary_user_cannot_manage_fields(self):
        self.client.force_login(self.ordinary_user)

        response = self.client.post(
            reverse('stadiums:field_create', args=[self.approved_stadium.pk]),
            self.field_payload(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Field.objects.exists())

    def test_stadium_admin_can_edit_disable_and_delete_own_field(self):
        field = Field.objects.create(
            stadium=self.approved_stadium,
            field_type='Basketball',
            number='A1',
            price_per_hour='80.00',
        )
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:field_edit', args=[field.pk]),
            self.field_payload(field_type='Tennis', number='T1', price_per_hour='120.00'),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:field_list', args=[self.approved_stadium.pk]))
        field.refresh_from_db()
        self.assertEqual(field.field_type, 'Tennis')
        self.assertEqual(field.number, 'T1')

        response = self.client.post(reverse('stadiums:field_disable', args=[field.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:field_list', args=[self.approved_stadium.pk]))
        field.refresh_from_db()
        self.assertFalse(field.is_active)

        response = self.client.post(reverse('stadiums:field_delete', args=[field.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:field_list', args=[self.approved_stadium.pk]))
        self.assertFalse(Field.objects.filter(pk=field.pk).exists())

    def test_public_detail_shows_only_active_fields(self):
        active = Field.objects.create(
            stadium=self.approved_stadium,
            field_type='Basketball',
            number='A1',
            price_per_hour='80.00',
        )
        inactive = Field.objects.create(
            stadium=self.approved_stadium,
            field_type='Tennis',
            number='T1',
            price_per_hour='120.00',
            is_active=False,
        )

        response = self.client.get(reverse('stadiums:detail', args=[self.approved_stadium.pk]))

        self.assertContains(response, active.number)
        self.assertContains(response, '80.00')
        self.assertNotContains(response, inactive.number)
        self.assertNotContains(response, '120.00')


class TimeSlotManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.stadium_admin = User.objects.create_user(
            phone_number='13300000001',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.other_stadium_admin = User.objects.create_user(
            phone_number='13300000002',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.ordinary_user = User.objects.create_user(
            phone_number='13300000003',
            password='pass',
            role=UserRole.ORDINARY,
        )
        self.stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Slot Stadium',
            address='Address',
            phone_number='13812345681',
            information='Info',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        self.other_stadium = Stadium.objects.create(
            owner=self.other_stadium_admin,
            name='Other Slot Stadium',
            address='Address',
            phone_number='13812345682',
            information='Info',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        self.field = Field.objects.create(
            stadium=self.stadium,
            field_type='Basketball',
            number='A1',
            price_per_hour='80.00',
        )
        self.other_field = Field.objects.create(
            stadium=self.other_stadium,
            field_type='Tennis',
            number='T1',
            price_per_hour='120.00',
        )

    def slot_payload(self, **overrides):
        payload = {
            'date': '2026-05-08',
            'start_time': '09:00',
            'end_time': '10:00',
            'is_available': 'on',
        }
        payload.update(overrides)
        return payload

    def test_stadium_admin_can_create_edit_and_delete_own_time_slot(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:time_slot_create', args=[self.field.pk]),
            self.slot_payload(),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:time_slot_list', args=[self.field.pk]))
        slot = TimeSlot.objects.get(field=self.field)
        self.assertEqual(slot.start_time, time(9, 0))
        self.assertTrue(slot.is_available)

        response = self.client.post(
            reverse('stadiums:time_slot_edit', args=[slot.pk]),
            self.slot_payload(start_time='10:00', end_time='11:00', is_available=''),
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:time_slot_list', args=[self.field.pk]))
        slot.refresh_from_db()
        self.assertEqual(slot.start_time, time(10, 0))
        self.assertFalse(slot.is_available)

        response = self.client.post(reverse('stadiums:time_slot_delete', args=[slot.pk]), follow=True)

        self.assertRedirects(response, reverse('stadiums:time_slot_list', args=[self.field.pk]))
        self.assertFalse(TimeSlot.objects.filter(pk=slot.pk).exists())

    def test_overlapping_time_slots_are_rejected_but_adjacent_slots_are_allowed(self):
        TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )

        with self.assertRaises(ValidationError):
            TimeSlot.objects.create(
                field=self.field,
                date=date(2026, 5, 8),
                start_time=time(10, 0),
                end_time=time(12, 0),
            )

        adjacent = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(11, 0),
            end_time=time(12, 0),
        )

        self.assertEqual(adjacent.start_time, time(11, 0))

    def test_overlapping_time_slot_form_returns_error(self):
        TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )
        self.client.force_login(self.stadium_admin)

        response = self.client.post(
            reverse('stadiums:time_slot_create', args=[self.field.pk]),
            self.slot_payload(start_time='10:00', end_time='12:00'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '同一场地同一天的开放时段不能重叠')
        self.assertEqual(TimeSlot.objects.count(), 1)

    def test_start_time_must_be_before_end_time(self):
        with self.assertRaises(ValidationError):
            TimeSlot.objects.create(
                field=self.field,
                date=date(2026, 5, 8),
                start_time=time(11, 0),
                end_time=time(11, 0),
            )

    def test_cannot_create_available_time_slot_for_inactive_field(self):
        self.field.is_active = False
        self.field.save(update_fields=['is_active'])

        with self.assertRaises(ValidationError):
            TimeSlot.objects.create(
                field=self.field,
                date=date(2026, 5, 8),
                start_time=time(9, 0),
                end_time=time(10, 0),
            )

    def test_non_owner_and_ordinary_user_cannot_manage_time_slots(self):
        self.client.force_login(self.stadium_admin)

        other_response = self.client.post(
            reverse('stadiums:time_slot_create', args=[self.other_field.pk]),
            self.slot_payload(),
        )

        self.assertEqual(other_response.status_code, 404)

        self.client.force_login(self.ordinary_user)
        ordinary_response = self.client.post(
            reverse('stadiums:time_slot_create', args=[self.field.pk]),
            self.slot_payload(),
        )

        self.assertEqual(ordinary_response.status_code, 403)
        self.assertFalse(TimeSlot.objects.exists())

    def test_public_detail_shows_only_available_time_slots(self):
        available = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        unavailable = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_available=False,
        )

        response = self.client.get(reverse('stadiums:detail', args=[self.stadium.pk]))

        self.assertContains(response, available.date.isoformat())
        self.assertContains(response, '09:00-10:00')
        self.assertNotContains(response, '10:00-11:00')
        self.assertFalse(unavailable.is_available)

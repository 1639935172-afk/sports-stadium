from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole

from .models import Stadium, StadiumAuditStatus


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

    def stadium_payload(self, **overrides):
        payload = {
            'name': '南航体育馆',
            'address': '南京市江宁区将军大道',
            'phone_number': '02512345678',
            'information': '综合体育场馆',
        }
        payload.update(overrides)
        return payload

    def create_pending_stadium(self, owner=None):
        return Stadium.objects.create(
            owner=owner or self.stadium_admin,
            **self.stadium_payload(),
        )

    def test_stadium_admin_can_submit_stadium_for_review(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(reverse('stadiums:create'), self.stadium_payload(), follow=True)

        self.assertRedirects(response, reverse('stadiums:my_stadiums'))
        stadium = Stadium.objects.get(name='南航体育馆')
        self.assertEqual(stadium.owner, self.stadium_admin)
        self.assertEqual(stadium.audit_status, StadiumAuditStatus.PENDING)
        self.assertFalse(stadium.is_open)

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

    def create_stadium(self, name, **overrides):
        data = {
            'owner': self.stadium_admin,
            'name': name,
            'address': f'{name} address',
            'phone_number': '02512345678',
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

        self.client.force_login(self.ordinary_user)
        list_response = self.client.get(reverse('stadiums:list'))
        detail_response = self.client.get(reverse('stadiums:detail', args=[stadium.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

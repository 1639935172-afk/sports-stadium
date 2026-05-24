from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from stadiums.models import Stadium, StadiumAuditStatus

from .models import Comment, CommentAuditStatus


class CommentWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ordinary_user = User.objects.create_user(
            phone_number='13500000001',
            password='pass',
            role=UserRole.ORDINARY,
            nickname='Comment User',
        )
        self.other_user = User.objects.create_user(
            phone_number='13500000002',
            password='pass',
            role=UserRole.ORDINARY,
        )
        self.stadium_admin = User.objects.create_user(
            phone_number='13500000003',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.system_admin = User.objects.create_user(
            phone_number='13500000004',
            password='pass',
            role=UserRole.SYSTEM_ADMIN,
        )
        self.stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Comment Stadium',
            address='Address',
            phone_number='13812345683',
            information='Info',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )

    def test_ordinary_user_can_submit_comment_as_pending(self):
        self.client.force_login(self.ordinary_user)

        response = self.client.post(
            reverse('comments:create', args=[self.stadium.pk]),
            {'content': 'Great court'},
            follow=True,
        )

        self.assertRedirects(response, reverse('stadiums:detail', args=[self.stadium.pk]))
        comment = Comment.objects.get(user=self.ordinary_user)
        self.assertEqual(comment.stadium, self.stadium)
        self.assertEqual(comment.content, 'Great court')
        self.assertEqual(comment.audit_status, CommentAuditStatus.PENDING)

    def test_non_ordinary_user_cannot_submit_comment(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(reverse('comments:create', args=[self.stadium.pk]), {'content': 'Nope'})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Comment.objects.exists())

    def test_cannot_comment_private_stadium(self):
        private_stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Private Stadium',
            address='Address',
            phone_number='13812345684',
            information='Info',
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
        )
        self.client.force_login(self.ordinary_user)

        response = self.client.post(reverse('comments:create', args=[private_stadium.pk]), {'content': 'Hidden'})

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.exists())

    def test_comment_model_rejects_non_ordinary_author(self):
        with self.assertRaises(ValidationError):
            Comment.objects.create(user=self.stadium_admin, stadium=self.stadium, content='Nope')

    def test_public_detail_shows_only_approved_comments(self):
        approved = Comment.objects.create(user=self.ordinary_user, stadium=self.stadium, content='Visible')
        approved.approve()
        pending = Comment.objects.create(user=self.other_user, stadium=self.stadium, content='Pending')
        rejected = Comment.objects.create(user=self.other_user, stadium=self.stadium, content='Rejected')
        rejected.reject()

        response = self.client.get(reverse('stadiums:detail', args=[self.stadium.pk]))

        self.assertContains(response, 'Visible')
        self.assertNotContains(response, pending.content)
        self.assertNotContains(response, rejected.content)

    def test_system_admin_can_approve_and_reject_comments(self):
        to_approve = Comment.objects.create(user=self.ordinary_user, stadium=self.stadium, content='Approve me')
        to_reject = Comment.objects.create(user=self.other_user, stadium=self.stadium, content='Reject me')
        self.client.force_login(self.system_admin)

        approve_response = self.client.post(reverse('comments:approve', args=[to_approve.pk]))
        reject_response = self.client.post(reverse('comments:reject', args=[to_reject.pk]))

        self.assertRedirects(approve_response, reverse('comments:audit_list'))
        self.assertRedirects(reject_response, reverse('comments:audit_list'))
        to_approve.refresh_from_db()
        to_reject.refresh_from_db()
        self.assertEqual(to_approve.audit_status, CommentAuditStatus.APPROVED)
        self.assertEqual(to_reject.audit_status, CommentAuditStatus.REJECTED)

    def test_non_system_admin_cannot_audit_comments(self):
        comment = Comment.objects.create(user=self.ordinary_user, stadium=self.stadium, content='Pending')
        self.client.force_login(self.stadium_admin)

        response = self.client.post(reverse('comments:approve', args=[comment.pk]))

        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.audit_status, CommentAuditStatus.PENDING)

    def test_user_can_delete_own_comment(self):
        comment = Comment.objects.create(user=self.ordinary_user, stadium=self.stadium, content='Mine')
        self.client.force_login(self.ordinary_user)

        response = self.client.post(reverse('comments:delete', args=[comment.pk]))

        self.assertRedirects(response, reverse('stadiums:detail', args=[self.stadium.pk]))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_user_cannot_delete_other_users_comment(self):
        comment = Comment.objects.create(user=self.other_user, stadium=self.stadium, content='Other')
        self.client.force_login(self.ordinary_user)

        response = self.client.post(reverse('comments:delete', args=[comment.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_system_admin_can_delete_any_comment(self):
        comment = Comment.objects.create(user=self.ordinary_user, stadium=self.stadium, content='Remove')
        self.client.force_login(self.system_admin)

        response = self.client.post(reverse('comments:delete', args=[comment.pk]))

        self.assertRedirects(response, reverse('comments:audit_list'))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

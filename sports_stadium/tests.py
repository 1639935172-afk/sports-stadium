from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from reservations.models import Reservation, ReservationStatus
from stadiums.models import Stadium


class HomePageTests(TestCase):
    def test_home_page_exposes_demo_workflow_entry_points(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '普通用户')
        self.assertContains(response, '场馆管理员')
        self.assertContains(response, '系统管理员')
        self.assertContains(response, reverse('stadiums:list'))


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_creates_repeatable_demo_dataset(self):
        call_command('seed_demo')
        call_command('seed_demo')

        User = get_user_model()
        self.assertTrue(User.objects.filter(phone_number='18800000001', role=UserRole.SYSTEM_ADMIN).exists())
        self.assertTrue(User.objects.filter(phone_number='18800000002', role=UserRole.STADIUM_ADMIN).exists())
        self.assertTrue(User.objects.filter(phone_number='18800000003', role=UserRole.ORDINARY).exists())
        self.assertTrue(Stadium.objects.filter(name='演示综合体育馆').exists())
        self.assertTrue(Reservation.objects.filter(status=ReservationStatus.PENDING).exists())

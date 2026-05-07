from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from stadiums.models import Field, Stadium, StadiumAuditStatus, TimeSlot

from .models import Reservation, ReservationStatus


class ReservationSubmissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            phone_number='13400000001',
            password='pass',
            role=UserRole.ORDINARY,
        )
        self.other_user = User.objects.create_user(
            phone_number='13400000002',
            password='pass',
            role=UserRole.ORDINARY,
        )
        self.stadium_admin = User.objects.create_user(
            phone_number='13400000003',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.stadium = Stadium.objects.create(
            owner=self.stadium_admin,
            name='Reservation Stadium',
            address='Address',
            phone_number='02512345678',
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
        self.time_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

    def test_ordinary_user_can_submit_reservation_and_status_is_pending(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reservations:create', args=[self.time_slot.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('reservations:mine'))
        reservation = Reservation.objects.get(user=self.user)
        self.assertEqual(reservation.time_slot, self.time_slot)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_anonymous_user_cannot_submit_reservation(self):
        response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])
        self.assertFalse(Reservation.objects.exists())

    def test_stadium_admin_cannot_submit_reservation(self):
        self.client.force_login(self.stadium_admin)

        response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Reservation.objects.exists())

    def test_unavailable_disabled_or_private_resources_cannot_be_reserved(self):
        self.client.force_login(self.user)

        self.time_slot.is_available = False
        self.time_slot.save()
        unavailable_response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]))
        self.assertEqual(unavailable_response.status_code, 404)

        self.time_slot.is_available = True
        self.time_slot.save()
        self.field.is_active = False
        self.field.save(update_fields=['is_active'])
        disabled_response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]))
        self.assertEqual(disabled_response.status_code, 404)

        self.field.is_active = True
        self.field.save(update_fields=['is_active'])
        self.stadium.audit_status = StadiumAuditStatus.PENDING
        self.stadium.is_open = False
        self.stadium.save(update_fields=['audit_status', 'is_open'])
        private_response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]))
        self.assertEqual(private_response.status_code, 404)
        self.assertFalse(Reservation.objects.exists())

    def test_user_cannot_submit_duplicate_active_reservation_for_same_slot(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)

        with self.assertRaises(ValidationError):
            Reservation.objects.create(user=self.user, time_slot=self.time_slot)

    def test_my_reservations_shows_only_current_user_reservations(self):
        own = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        other_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 5, 8),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        other = Reservation.objects.create(user=self.other_user, time_slot=other_slot)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reservations:mine'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own.time_slot.field.stadium.name)
        self.assertContains(response, '09:00-10:00')
        self.assertNotContains(response, '10:00-11:00')
        self.assertNotContains(response, str(other.user.phone_number))

    def test_public_stadium_detail_contains_booking_button_for_ordinary_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('stadiums:detail', args=[self.stadium.pk]))

        self.assertContains(response, reverse('reservations:create', args=[self.time_slot.pk]))
        self.assertContains(response, '预约')

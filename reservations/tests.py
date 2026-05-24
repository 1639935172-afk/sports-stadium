from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from stadiums.models import Field, Stadium, StadiumAuditStatus, TimeSlot

from .models import PaymentStatus, Reservation, ReservationStatus


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
            phone_number='13812345678',
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
            date=date(2026, 6, 8),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

    def test_ordinary_user_can_submit_reservation_and_status_is_awaiting_payment(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]), follow=True)

        self.assertRedirects(response, reverse('reservations:mine'))
        reservation = Reservation.objects.get(user=self.user)
        self.assertEqual(reservation.time_slot, self.time_slot)
        self.assertEqual(reservation.status, ReservationStatus.AWAITING_PAYMENT)
        self.assertEqual(reservation.payment.status, PaymentStatus.UNPAID)
        self.assertEqual(str(reservation.payment.amount), str(self.field.price_per_hour))

    def test_user_can_pay_awaiting_payment_reservation_then_it_enters_pending_review(self):
        reservation = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        reservation.ensure_payment()
        self.client.force_login(self.user)

        response = self.client.post(reverse('reservations:pay', args=[reservation.pk]), follow=True)

        self.assertRedirects(response, reverse('reservations:mine'))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertEqual(reservation.payment.status, PaymentStatus.PAID)

    def test_user_can_mark_payment_failed_and_release_slot(self):
        reservation = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        reservation.ensure_payment()
        self.client.force_login(self.user)

        response = self.client.post(reverse('reservations:payment_fail', args=[reservation.pk]), follow=True)

        self.assertRedirects(response, reverse('reservations:mine'))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.PAYMENT_FAILED)
        self.assertEqual(reservation.payment.status, PaymentStatus.FAILED)
        new_reservation = Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)
        self.assertEqual(new_reservation.status, ReservationStatus.AWAITING_PAYMENT)

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

    def test_pending_reservation_blocks_other_users_from_booking_same_slot(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.client.force_login(self.other_user)

        response = self.client.post(reverse('reservations:create', args=[self.time_slot.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_model_rejects_other_user_when_slot_has_pending_or_approved_reservation(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)

        with self.assertRaises(ValidationError):
            Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)

    def test_rejected_reservation_releases_slot_for_other_user(self):
        reservation = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        reservation.reject()

        new_reservation = Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)

        self.assertEqual(new_reservation.status, ReservationStatus.AWAITING_PAYMENT)

    def test_my_reservations_shows_only_current_user_reservations(self):
        own = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        other_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 6, 8),
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

    def test_public_stadium_detail_hides_occupied_slot_booking_button(self):
        Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        self.client.force_login(self.other_user)

        response = self.client.get(reverse('stadiums:detail', args=[self.stadium.pk]))

        self.assertNotContains(response, reverse('reservations:create', args=[self.time_slot.pk]))

    def test_stadium_admin_can_view_only_owned_pending_reservations(self):
        own_reservation = Reservation.objects.create(
            user=self.user,
            time_slot=self.time_slot,
            status=ReservationStatus.PENDING,
        )
        other_admin = get_user_model().objects.create_user(
            phone_number='13400000004',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        other_stadium = Stadium.objects.create(
            owner=other_admin,
            name='Other Stadium',
            address='Other Address',
            phone_number='13887654321',
            information='Info',
            audit_status=StadiumAuditStatus.APPROVED,
            is_open=True,
        )
        other_field = Field.objects.create(
            stadium=other_stadium,
            field_type='Badminton',
            number='B1',
            price_per_hour='60.00',
        )
        other_slot = TimeSlot.objects.create(
            field=other_field,
            date=date(2026, 6, 8),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        other_reservation = Reservation.objects.create(
            user=self.other_user,
            time_slot=other_slot,
            status=ReservationStatus.PENDING,
        )
        self.client.force_login(self.stadium_admin)

        response = self.client.get(reverse('reservations:admin_pending'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_reservation.user.phone_number)
        self.assertContains(response, '2026-06-08')
        self.assertNotContains(response, other_reservation.user.phone_number)

    def test_stadium_admin_pending_list_hides_expired_reservations(self):
        expired_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 6, 9),
            start_time=time(8, 0),
            end_time=time(9, 0),
        )
        expired_reservation = Reservation.objects.create(
            user=self.user,
            time_slot=expired_slot,
            status=ReservationStatus.PENDING,
        )
        TimeSlot.objects.filter(pk=expired_slot.pk).update(date=date(2026, 5, 19))
        self.client.force_login(self.stadium_admin)

        response = self.client.get(reverse('reservations:admin_pending'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '2026-05-19')
        self.assertNotContains(response, expired_reservation.user.phone_number)

    def test_stadium_admin_can_approve_and_reject_owned_pending_reservations(self):
        to_approve = Reservation.objects.create(
            user=self.user,
            time_slot=self.time_slot,
            status=ReservationStatus.PENDING,
        )
        other_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 6, 8),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        to_reject = Reservation.objects.create(
            user=self.other_user,
            time_slot=other_slot,
            status=ReservationStatus.PENDING,
        )
        self.client.force_login(self.stadium_admin)

        approve_response = self.client.post(reverse('reservations:approve', args=[to_approve.pk]))
        reject_response = self.client.post(reverse('reservations:reject', args=[to_reject.pk]))

        self.assertRedirects(approve_response, reverse('reservations:admin_pending'))
        self.assertRedirects(reject_response, reverse('reservations:admin_pending'))
        to_approve.refresh_from_db()
        to_reject.refresh_from_db()
        self.assertEqual(to_approve.status, ReservationStatus.APPROVED)
        self.assertEqual(to_reject.status, ReservationStatus.REJECTED)

    def test_non_owner_cannot_review_reservation(self):
        reservation = Reservation.objects.create(
            user=self.user,
            time_slot=self.time_slot,
            status=ReservationStatus.PENDING,
        )
        other_admin = get_user_model().objects.create_user(
            phone_number='13400000005',
            password='pass',
            role=UserRole.STADIUM_ADMIN,
        )
        self.client.force_login(other_admin)

        response = self.client.post(reverse('reservations:approve', args=[reservation.pk]))

        self.assertEqual(response.status_code, 404)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_approve_fails_when_slot_already_has_approved_reservation(self):
        approved = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        approved.approve()
        with self.assertRaises(ValidationError):
            Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)

    def test_user_can_cancel_own_pending_or_approved_reservation(self):
        pending = Reservation.objects.create(
            user=self.user,
            time_slot=self.time_slot,
            status=ReservationStatus.PENDING,
        )
        other_slot = TimeSlot.objects.create(
            field=self.field,
            date=date(2026, 6, 8),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        approved = Reservation.objects.create(user=self.user, time_slot=other_slot)
        approved.approve()
        self.client.force_login(self.user)

        self.client.post(reverse('reservations:cancel', args=[pending.pk]))
        self.client.post(reverse('reservations:cancel', args=[approved.pk]))

        pending.refresh_from_db()
        approved.refresh_from_db()
        self.assertEqual(pending.status, ReservationStatus.CANCELLED)
        self.assertEqual(approved.status, ReservationStatus.CANCELLED)

    def test_cancelled_reservation_no_longer_blocks_slot_approval(self):
        cancelled = Reservation.objects.create(user=self.user, time_slot=self.time_slot)
        cancelled.approve()
        cancelled.cancel()
        pending = Reservation.objects.create(
            user=self.other_user,
            time_slot=self.time_slot,
            status=ReservationStatus.PENDING,
        )

        pending.approve()

        pending.refresh_from_db()
        self.assertEqual(pending.status, ReservationStatus.APPROVED)

    def test_user_cannot_cancel_other_users_reservation(self):
        reservation = Reservation.objects.create(user=self.other_user, time_slot=self.time_slot)
        self.client.force_login(self.user)

        response = self.client.post(reverse('reservations:cancel', args=[reservation.pk]))

        self.assertEqual(response.status_code, 404)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.AWAITING_PAYMENT)

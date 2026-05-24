from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required
from stadiums.models import StadiumAuditStatus, TimeSlot

from .models import Reservation, ReservationStatus


def _bookable_time_slots():
    now = timezone.localtime()
    occupied_slot_ids = Reservation.objects.filter(
        status__in=Reservation.occupying_statuses(),
    ).values('time_slot_id')
    return TimeSlot.objects.filter(
        is_available=True,
        field__is_active=True,
        field__stadium__audit_status=StadiumAuditStatus.APPROVED,
        field__stadium__is_open=True,
        field__stadium__deletion_requested=False,
    ).filter(
        Q(date__gt=now.date()) | Q(date=now.date(), start_time__gt=now.time())
    ).exclude(pk__in=occupied_slot_ids)


def _future_slot_filter():
    now = timezone.localtime()
    return Q(time_slot__date__gt=now.date()) | Q(
        time_slot__date=now.date(),
        time_slot__start_time__gt=now.time(),
    )


@login_required
@role_required(UserRole.ORDINARY)
@require_POST
def reservation_create_view(request, slot_pk):
    time_slot = get_object_or_404(_bookable_time_slots(), pk=slot_pk)
    reservation = Reservation(user=request.user, time_slot=time_slot)
    try:
        reservation.save()
        reservation.ensure_payment()
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, '预约已创建，请先完成支付')
    return redirect('reservations:mine')


@login_required
@role_required(UserRole.ORDINARY)
def my_reservations_view(request):
    reservations = (
        Reservation.objects.filter(user=request.user)
        .select_related('time_slot__field__stadium', 'payment')
        .order_by('-created_at')
    )
    return render(request, 'reservations/my_reservations.html', {'reservations': reservations})


def _admin_reservations(user):
    return Reservation.objects.filter(time_slot__field__stadium__owner=user)


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def admin_pending_reservations_view(request):
    reservations = (
        _admin_reservations(request.user)
        .filter(status=ReservationStatus.PENDING)
        .filter(_future_slot_filter())
        .select_related('user', 'time_slot__field__stadium', 'payment')
        .order_by('created_at')
    )
    return render(request, 'reservations/admin_pending.html', {'reservations': reservations})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def reservation_approve_view(request, pk):
    reservation = get_object_or_404(
        _admin_reservations(request.user).select_related('time_slot__field__stadium'),
        _future_slot_filter(),
        pk=pk,
        status=ReservationStatus.PENDING,
    )
    try:
        reservation.approve()
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, '预约已通过')
    return redirect('reservations:admin_pending')


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def reservation_reject_view(request, pk):
    reservation = get_object_or_404(
        _admin_reservations(request.user),
        _future_slot_filter(),
        pk=pk,
        status=ReservationStatus.PENDING,
    )
    reservation.reject()
    messages.success(request, '预约已拒绝')
    return redirect('reservations:admin_pending')


@login_required
@role_required(UserRole.ORDINARY)
@require_POST
def reservation_cancel_view(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    try:
        reservation.cancel()
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, '预约已取消')
    return redirect('reservations:mine')


@login_required
@role_required(UserRole.ORDINARY)
@require_POST
def reservation_pay_view(request, pk):
    reservation = get_object_or_404(Reservation.objects.select_related('payment'), pk=pk, user=request.user)
    try:
        reservation.mark_payment_paid()
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, '支付成功，预约已进入待审核')
    return redirect('reservations:mine')


@login_required
@role_required(UserRole.ORDINARY)
@require_POST
def reservation_payment_fail_view(request, pk):
    reservation = get_object_or_404(Reservation.objects.select_related('payment'), pk=pk, user=request.user)
    try:
        reservation.mark_payment_failed()
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, '支付失败，预约已关闭')
    return redirect('reservations:mine')

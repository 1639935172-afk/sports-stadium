from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required
from stadiums.models import StadiumAuditStatus, TimeSlot

from .models import Reservation, ReservationStatus


def _bookable_time_slots():
    occupied_slot_ids = Reservation.objects.filter(
        status__in=Reservation.occupying_statuses(),
    ).values('time_slot_id')
    return TimeSlot.objects.filter(
        is_available=True,
        field__is_active=True,
        field__stadium__audit_status=StadiumAuditStatus.APPROVED,
        field__stadium__is_open=True,
        field__stadium__deletion_requested=False,
    ).exclude(pk__in=occupied_slot_ids)


@login_required
@role_required(UserRole.ORDINARY)
@require_POST
def reservation_create_view(request, slot_pk):
    time_slot = get_object_or_404(_bookable_time_slots(), pk=slot_pk)
    reservation = Reservation(user=request.user, time_slot=time_slot)
    try:
        reservation.save()
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages))
    else:
        messages.success(request, '预约已提交，等待场馆管理员审核')
    return redirect('reservations:mine')


@login_required
@role_required(UserRole.ORDINARY)
def my_reservations_view(request):
    reservations = (
        Reservation.objects.filter(user=request.user)
        .select_related('time_slot__field__stadium')
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
        .select_related('user', 'time_slot__field__stadium')
        .order_by('created_at')
    )
    return render(request, 'reservations/admin_pending.html', {'reservations': reservations})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def reservation_approve_view(request, pk):
    reservation = get_object_or_404(
        _admin_reservations(request.user).select_related('time_slot__field__stadium'),
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

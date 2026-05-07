from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required
from stadiums.models import StadiumAuditStatus, TimeSlot

from .models import Reservation


def _bookable_time_slots():
    return TimeSlot.objects.filter(
        is_available=True,
        field__is_active=True,
        field__stadium__audit_status=StadiumAuditStatus.APPROVED,
        field__stadium__is_open=True,
        field__stadium__deletion_requested=False,
    )


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
        messages.success(request, '预约申请已提交，等待场馆管理员审核')
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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required

from .forms import FieldForm, StadiumForm, TimeSlotForm
from .models import Field, Stadium, StadiumAuditStatus, TimeSlot


def _public_stadiums():
    return Stadium.objects.filter(
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


def stadium_list_view(request):
    query = request.GET.get('q', '').strip()
    stadiums = _public_stadiums()
    if query:
        stadiums = stadiums.filter(name__icontains=query)

    return render(
        request,
        'stadiums/stadium_list.html',
        {
            'stadiums': stadiums,
            'query': query,
        },
    )


def stadium_detail_view(request, pk):
    stadium = get_object_or_404(_public_stadiums(), pk=pk)
    fields = stadium.fields.filter(is_active=True).prefetch_related(
        Prefetch('time_slots', queryset=TimeSlot.objects.filter(is_available=True), to_attr='available_time_slots')
    )
    return render(request, 'stadiums/stadium_detail.html', {'stadium': stadium, 'fields': fields})


def _owned_approved_stadiums(user):
    return Stadium.objects.filter(
        owner=user,
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def my_stadiums_view(request):
    stadiums = Stadium.objects.filter(owner=request.user)
    return render(request, 'stadiums/my_stadiums.html', {'stadiums': stadiums})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def stadium_create_view(request):
    form = StadiumForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        stadium = form.save(commit=False)
        stadium.owner = request.user
        stadium.audit_status = StadiumAuditStatus.PENDING
        stadium.is_open = False
        stadium.save()
        messages.success(request, '场馆已提交审核')
        return redirect('stadiums:my_stadiums')

    return render(request, 'stadiums/stadium_form.html', {'form': form, 'title': '提交场馆'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def stadium_edit_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, owner=request.user)
    form = StadiumForm(request.POST or None, instance=stadium)
    if request.method == 'POST' and form.is_valid():
        stadium = form.save(commit=False)
        stadium.audit_status = StadiumAuditStatus.PENDING
        stadium.is_open = False
        stadium.deletion_requested = False
        stadium.save()
        messages.success(request, '场馆修改已重新提交审核')
        return redirect('stadiums:my_stadiums')

    return render(request, 'stadiums/stadium_form.html', {'form': form, 'title': '修改场馆'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def stadium_delete_request_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, owner=request.user)
    stadium.request_deletion()
    messages.success(request, '删除申请已提交审核')
    return redirect('stadiums:my_stadiums')


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def field_list_view(request, stadium_pk):
    stadium = get_object_or_404(_owned_approved_stadiums(request.user), pk=stadium_pk)
    fields = stadium.fields.all()
    return render(request, 'stadiums/field_list.html', {'stadium': stadium, 'fields': fields})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def field_create_view(request, stadium_pk):
    stadium = get_object_or_404(_owned_approved_stadiums(request.user), pk=stadium_pk)
    form = FieldForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        field = form.save(commit=False)
        field.stadium = stadium
        field.save()
        messages.success(request, '场地已创建')
        return redirect('stadiums:field_list', stadium_pk=stadium.pk)

    return render(request, 'stadiums/field_form.html', {'form': form, 'stadium': stadium, 'title': '新增场地'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def field_edit_view(request, pk):
    field = get_object_or_404(Field, pk=pk, stadium__owner=request.user)
    form = FieldForm(request.POST or None, instance=field)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '场地信息已更新')
        return redirect('stadiums:field_list', stadium_pk=field.stadium_id)

    return render(request, 'stadiums/field_form.html', {'form': form, 'stadium': field.stadium, 'title': '编辑场地'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def field_disable_view(request, pk):
    field = get_object_or_404(Field, pk=pk, stadium__owner=request.user)
    field.is_active = False
    field.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, '场地已停用')
    return redirect('stadiums:field_list', stadium_pk=field.stadium_id)


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def field_delete_view(request, pk):
    field = get_object_or_404(Field, pk=pk, stadium__owner=request.user)
    stadium_pk = field.stadium_id
    field.delete()
    messages.success(request, '场地已删除')
    return redirect('stadiums:field_list', stadium_pk=stadium_pk)


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def time_slot_list_view(request, field_pk):
    field = get_object_or_404(Field, pk=field_pk, stadium__owner=request.user)
    time_slots = field.time_slots.all()
    return render(request, 'stadiums/time_slot_list.html', {'field': field, 'time_slots': time_slots})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def time_slot_create_view(request, field_pk):
    field = get_object_or_404(Field, pk=field_pk, stadium__owner=request.user, is_active=True)
    form = TimeSlotForm(request.POST or None, field=field)
    if request.method == 'POST' and form.is_valid():
        time_slot = form.save(commit=False)
        time_slot.field = field
        time_slot.save()
        messages.success(request, '时段已创建')
        return redirect('stadiums:time_slot_list', field_pk=field.pk)

    return render(request, 'stadiums/time_slot_form.html', {'form': form, 'field': field, 'title': '新增时段'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def time_slot_edit_view(request, pk):
    time_slot = get_object_or_404(TimeSlot, pk=pk, field__stadium__owner=request.user)
    form = TimeSlotForm(request.POST or None, instance=time_slot)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '时段已更新')
        return redirect('stadiums:time_slot_list', field_pk=time_slot.field_id)

    return render(request, 'stadiums/time_slot_form.html', {'form': form, 'field': time_slot.field, 'title': '编辑时段'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def time_slot_delete_view(request, pk):
    time_slot = get_object_or_404(TimeSlot, pk=pk, field__stadium__owner=request.user)
    field_pk = time_slot.field_id
    time_slot.delete()
    messages.success(request, '时段已删除')
    return redirect('stadiums:time_slot_list', field_pk=field_pk)


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
def audit_list_view(request):
    stadiums = Stadium.objects.filter(audit_status=StadiumAuditStatus.PENDING)
    return render(request, 'stadiums/audit_list.html', {'stadiums': stadiums})


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
@require_POST
def audit_approve_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, audit_status=StadiumAuditStatus.PENDING)
    result = stadium.approve()
    if result == 'deleted':
        messages.success(request, '场馆删除申请已通过，场馆已删除')
    else:
        messages.success(request, '场馆审核已通过')
    return redirect('stadiums:audit_list')


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
@require_POST
def audit_reject_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, audit_status=StadiumAuditStatus.PENDING)
    stadium.reject()
    messages.success(request, '场馆申请已退回')
    return redirect('stadiums:audit_list')

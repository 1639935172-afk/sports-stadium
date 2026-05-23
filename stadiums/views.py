from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required

from .forms import FieldForm, StadiumCoverForm, StadiumForm, TimeSlotForm
from comments.forms import CommentForm
from comments.models import CommentAuditStatus
from reservations.models import Reservation

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
        stadiums = stadiums.filter(
            Q(name__icontains=query)
            | Q(fields__field_type__icontains=query, fields__is_active=True)
            | Q(fields__number__icontains=query, fields__is_active=True)
        ).distinct()

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
    fields, comments, comment_form = _build_stadium_detail_context(stadium, request.user)
    return render(
        request,
        'stadiums/stadium_detail.html',
        {'stadium': stadium, 'fields': fields, 'comments': comments, 'comment_form': comment_form},
    )


def _owned_approved_stadiums(user):
    return Stadium.objects.filter(
        owner=user,
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


def _build_stadium_detail_context(stadium, user):
    occupied_slot_ids = Reservation.objects.filter(
        status__in=Reservation.occupying_statuses(),
    ).values('time_slot_id')
    available_slots = TimeSlot.objects.filter(is_available=True).exclude(pk__in=occupied_slot_ids)
    fields = stadium.fields.filter(is_active=True).prefetch_related(
        Prefetch('time_slots', queryset=available_slots, to_attr='available_time_slots')
    )
    comments = stadium.comments.filter(audit_status=CommentAuditStatus.APPROVED).select_related('user')
    comment_form = CommentForm() if user.is_authenticated and user.is_ordinary_user else None
    return fields, comments, comment_form


def _render_my_stadiums_page(
    request,
    *,
    form=None,
    show_create_modal=False,
    show_edit_modal=False,
    show_preview_modal=False,
    edit_stadium=None,
    preview_stadium=None,
    preview_cover_form=None,
):
    stadiums = Stadium.objects.filter(owner=request.user)
    if show_edit_modal and edit_stadium is None:
        edit_stadium_id = request.GET.get('edit')
        if edit_stadium_id:
            edit_stadium = get_object_or_404(Stadium, pk=edit_stadium_id, owner=request.user)
    if show_preview_modal and preview_stadium is None:
        preview_stadium_id = request.GET.get('preview')
        if preview_stadium_id:
            preview_stadium = get_object_or_404(Stadium, pk=preview_stadium_id, owner=request.user)
    modal_form = form or (StadiumForm(instance=edit_stadium) if show_edit_modal and edit_stadium else StadiumForm())
    cover_form = preview_cover_form or (StadiumCoverForm(instance=preview_stadium) if preview_stadium else StadiumCoverForm())
    preview_fields = preview_comments = preview_comment_form = None
    if show_preview_modal and preview_stadium is not None:
        preview_fields, preview_comments, preview_comment_form = _build_stadium_detail_context(
            preview_stadium,
            request.user,
        )
    return render(
        request,
        'stadiums/my_stadiums.html',
        {
            'stadiums': stadiums,
            'stadium_modal_form': modal_form,
            'show_create_modal': show_create_modal,
            'show_edit_modal': show_edit_modal,
            'show_preview_modal': show_preview_modal,
            'edit_stadium': edit_stadium,
            'preview_stadium': preview_stadium,
            'preview_cover_form': cover_form,
            'preview_fields': preview_fields,
            'preview_comments': preview_comments,
            'preview_comment_form': preview_comment_form,
        },
    )


def _render_field_list_page(request, stadium, *, form=None, show_edit_modal=False, edit_field=None):
    fields = stadium.fields.all()
    if show_edit_modal and edit_field is None:
        edit_field_id = request.GET.get('edit')
        if edit_field_id:
            edit_field = get_object_or_404(Field, pk=edit_field_id, stadium__owner=request.user, stadium=stadium)
    modal_form = form or (FieldForm(instance=edit_field) if show_edit_modal and edit_field else FieldForm())
    return render(
        request,
        'stadiums/field_list.html',
        {
            'stadium': stadium,
            'fields': fields,
            'field_modal_form': modal_form,
            'show_edit_field_modal': show_edit_modal,
            'edit_field': edit_field,
        },
    )


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def my_stadiums_view(request):
    modal = request.GET.get('modal')
    if modal == 'create':
        return _render_my_stadiums_page(request, show_create_modal=True)
    if modal == 'edit':
        return _render_my_stadiums_page(request, show_edit_modal=True)
    if modal == 'preview':
        return _render_my_stadiums_page(request, show_preview_modal=True)
    return _render_my_stadiums_page(request)


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def stadium_create_view(request):
    form = StadiumForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        stadium = form.save(commit=False)
        stadium.owner = request.user
        stadium.audit_status = StadiumAuditStatus.PENDING
        stadium.is_open = False
        stadium.save()
        messages.success(request, '场馆已提交审核')
        return redirect('stadiums:my_stadiums')

    return _render_my_stadiums_page(request, form=form, show_create_modal=True)


@login_required
@role_required(UserRole.STADIUM_ADMIN)
@require_POST
def stadium_cover_update_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, owner=request.user)
    form = StadiumCoverForm(request.POST or None, request.FILES or None, instance=stadium)
    if form.is_valid():
        form.save()
        messages.success(request, '场馆照片已更新')
        return redirect(f"{reverse('stadiums:my_stadiums')}?modal=preview&preview={stadium.pk}")

    return _render_my_stadiums_page(
        request,
        show_preview_modal=True,
        preview_stadium=stadium,
        preview_cover_form=form,
    )


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def stadium_edit_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, owner=request.user)
    form = StadiumForm(request.POST or None, request.FILES or None, instance=stadium)
    if request.method == 'POST' and form.is_valid():
        stadium = form.save(commit=False)
        stadium.audit_status = StadiumAuditStatus.PENDING
        stadium.is_open = False
        stadium.deletion_requested = False
        stadium.save()
        messages.success(request, '场馆修改已提交审核')
        return redirect('stadiums:my_stadiums')

    return _render_my_stadiums_page(request, form=form, show_edit_modal=True, edit_stadium=stadium)



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
@require_POST
def stadium_delete_request_cancel_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, owner=request.user, deletion_requested=True)
    stadium.cancel_deletion_request()
    messages.success(request, '已撤销删除申请')
    return redirect('stadiums:my_stadiums')


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def field_list_view(request, stadium_pk):
    stadium = get_object_or_404(_owned_approved_stadiums(request.user), pk=stadium_pk)
def field_list_view(request, stadium_pk):
    stadium = get_object_or_404(_owned_approved_stadiums(request.user), pk=stadium_pk)
    show_edit_modal = request.GET.get('modal') == 'edit'
    return _render_field_list_page(request, stadium, show_edit_modal=show_edit_modal)
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

    return render(request, 'stadiums/field_form.html', {'form': form, 'stadium': stadium, 'title': '添加场地'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def field_edit_view(request, pk):
    field = get_object_or_404(Field, pk=pk, stadium__owner=request.user)
    form = FieldForm(request.POST or None, instance=field)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '场地已更新')
        return redirect('stadiums:field_list', stadium_pk=field.stadium_id)

    return _render_field_list_page(request, field.stadium, form=form, show_edit_modal=True, edit_field=field)


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
    time_slots = list(field.time_slots.all())
    occupied_slot_ids = set(
        Reservation.objects.filter(
            time_slot__field=field,
            status__in=Reservation.occupying_statuses(),
        ).values_list('time_slot_id', flat=True)
    )
    for slot in time_slots:
        slot.actual_is_available = slot.is_available and slot.pk not in occupied_slot_ids
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

    return render(request, 'stadiums/time_slot_form.html', {'form': form, 'field': field, 'title': '添加时段'})


@login_required
@role_required(UserRole.STADIUM_ADMIN)
def time_slot_edit_view(request, pk):
    time_slot = get_object_or_404(TimeSlot, pk=pk, field__stadium__owner=request.user)
    form = TimeSlotForm(request.POST or None, instance=time_slot)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '时段已更新')
        return redirect('stadiums:time_slot_list', field_pk=time_slot.field_id)

    return render(request, 'stadiums/time_slot_form.html', {'form': form, 'field': time_slot.field, 'title': '修改时段'})


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
        messages.success(request, '鍦洪鍒犻櫎鐢宠宸查€氳繃锛屽満棣嗗凡鍒犻櫎')
    else:
        messages.success(request, '鍦洪瀹℃牳宸查€氳繃')
    return redirect('stadiums:audit_list')


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
@require_POST
def audit_reject_view(request, pk):
    stadium = get_object_or_404(Stadium, pk=pk, audit_status=StadiumAuditStatus.PENDING)
    stadium.reject()
    messages.success(request, '场馆审核已拒绝')
    return redirect('stadiums:audit_list')



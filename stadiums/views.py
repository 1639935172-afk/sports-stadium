from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required

from .forms import StadiumForm
from .models import Stadium, StadiumAuditStatus


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
    return render(request, 'stadiums/stadium_detail.html', {'stadium': stadium})


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

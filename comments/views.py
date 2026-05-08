from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserRole
from accounts.permissions import role_required
from stadiums.models import Stadium, StadiumAuditStatus

from .forms import CommentForm
from .models import Comment, CommentAuditStatus


def _public_stadiums():
    return Stadium.objects.filter(
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


@login_required
@role_required(UserRole.ORDINARY)
@require_POST
def comment_create_view(request, stadium_pk):
    stadium = get_object_or_404(_public_stadiums(), pk=stadium_pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.stadium = stadium
        comment.audit_status = CommentAuditStatus.PENDING
        comment.save()
        messages.success(request, '评论已提交，等待审核')
    else:
        messages.error(request, '评论提交失败，请检查内容')
    return redirect('stadiums:detail', pk=stadium.pk)


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
def comment_audit_list_view(request):
    comments = (
        Comment.objects.filter(audit_status=CommentAuditStatus.PENDING)
        .select_related('user', 'stadium')
        .order_by('created_at')
    )
    return render(request, 'comments/audit_list.html', {'comments': comments})


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
@require_POST
def comment_approve_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk, audit_status=CommentAuditStatus.PENDING)
    comment.approve()
    messages.success(request, '评论已通过')
    return redirect('comments:audit_list')


@login_required
@role_required(UserRole.SYSTEM_ADMIN)
@require_POST
def comment_reject_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk, audit_status=CommentAuditStatus.PENDING)
    comment.reject()
    messages.success(request, '评论已拒绝')
    return redirect('comments:audit_list')


@login_required
@require_POST
def comment_delete_view(request, pk):
    queryset = Comment.objects.all()
    if request.user.role == UserRole.ORDINARY:
        queryset = queryset.filter(user=request.user)
    elif request.user.role != UserRole.SYSTEM_ADMIN:
        queryset = queryset.none()

    comment = get_object_or_404(queryset, pk=pk)
    stadium_pk = comment.stadium_id
    comment.delete()
    messages.success(request, '评论已删除')

    if request.user.role == UserRole.SYSTEM_ADMIN:
        return redirect('comments:audit_list')
    return redirect('stadiums:detail', pk=stadium_pk)

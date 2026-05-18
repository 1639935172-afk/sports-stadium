from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from comments.models import Comment, CommentAuditStatus
from reservations.models import Reservation
from reservations.models import ReservationStatus
from stadiums.models import Field, Stadium, StadiumAuditStatus, TimeSlot

from .serializers import (
    AccountCancelSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ReservationCreateSerializer,
    ReservationSerializer,
    FieldManageSerializer,
    StadiumAuditSerializer,
    StadiumDetailSerializer,
    StadiumListSerializer,
    StadiumManageSerializer,
    TimeSlotManageSerializer,
    SystemUserUpdateSerializer,
    UserSerializer,
)


class IsOrdinaryUser(permissions.BasePermission):
    message = '只有普通用户可以执行该操作。'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ORDINARY)


class IsSystemAdmin(permissions.BasePermission):
    message = '只有系统管理员可以执行该操作。'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.SYSTEM_ADMIN)


class IsStadiumAdmin(permissions.BasePermission):
    message = '只有场馆管理员可以执行该操作。'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.STADIUM_ADMIN)


def public_stadiums():
    return Stadium.objects.filter(
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


def pending_stadiums():
    return Stadium.objects.filter(
        audit_status=StadiumAuditStatus.PENDING,
    ).select_related('owner')


def owned_approved_stadiums(user):
    return Stadium.objects.filter(
        owner=user,
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


def owned_fields(user):
    return Field.objects.filter(
        stadium__owner=user,
        stadium__audit_status=StadiumAuditStatus.APPROVED,
        stadium__is_open=True,
        stadium__deletion_requested=False,
    ).select_related('stadium')


def owned_active_fields(user):
    return owned_fields(user).filter(is_active=True)


def owned_time_slots(user):
    return TimeSlot.objects.filter(
        field__stadium__owner=user,
        field__stadium__audit_status=StadiumAuditStatus.APPROVED,
        field__stadium__is_open=True,
        field__stadium__deletion_requested=False,
    ).select_related('field', 'field__stadium')


def serializer_error(exc):
    if hasattr(exc, 'message_dict'):
        return exc.message_dict
    if hasattr(exc, 'messages'):
        return exc.messages
    return str(exc)


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in {'PUT', 'PATCH'}:
            return ProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(request.user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class SystemUserListView(generics.ListAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = get_user_model().objects.all().order_by('phone_number')
        q = self.request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(phone_number__icontains=q) | Q(nickname__icontains=q)
            )
        return queryset


class SystemUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = SystemUserUpdateSerializer
    queryset = get_user_model().objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response({'detail': '不能在这里管理自己的账号。'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class AccountCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AccountCancelSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class StadiumListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StadiumListSerializer

    def get_queryset(self):
        queryset = public_stadiums()
        q = self.request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(address__icontains=q))
        return queryset.order_by('name')


class StadiumMineView(generics.ListCreateAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = StadiumManageSerializer

    def get_queryset(self):
        return Stadium.objects.filter(owner=self.request.user).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user,
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
            deletion_requested=False,
        )


class StadiumMineDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = StadiumManageSerializer

    def get_queryset(self):
        return Stadium.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save(
            audit_status=StadiumAuditStatus.PENDING,
            is_open=False,
            deletion_requested=False,
        )


class StadiumMineDeleteRequestView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request, pk):
        stadium = get_object_or_404(Stadium, pk=pk, owner=request.user)
        stadium.request_deletion()
        return Response(StadiumManageSerializer(stadium).data)


class FieldManageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = FieldManageSerializer

    def get_queryset(self):
        stadium = get_object_or_404(
            owned_approved_stadiums(self.request.user),
            pk=self.kwargs['stadium_pk'],
        )
        return stadium.fields.all().order_by('number')

    def perform_create(self, serializer):
        stadium = get_object_or_404(
            owned_approved_stadiums(self.request.user),
            pk=self.kwargs['stadium_pk'],
        )
        serializer.save(stadium=stadium)


class FieldManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = FieldManageSerializer

    def get_queryset(self):
        return owned_fields(self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FieldDisableView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request, pk):
        field = get_object_or_404(owned_fields(request.user), pk=pk)
        field.is_active = False
        field.save(update_fields=['is_active', 'updated_at'])
        return Response(FieldManageSerializer(field).data)


class TimeSlotManageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = TimeSlotManageSerializer

    def get_queryset(self):
        field = get_object_or_404(
            owned_fields(self.request.user),
            pk=self.kwargs['field_pk'],
        )
        return field.time_slots.all().order_by('date', 'start_time')

    def perform_create(self, serializer):
        field = get_object_or_404(
            owned_active_fields(self.request.user),
            pk=self.kwargs['field_pk'],
        )
        serializer.save(field=field)


class TimeSlotManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = TimeSlotManageSerializer

    def get_queryset(self):
        return owned_time_slots(self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StadiumDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StadiumDetailSerializer

    def get_queryset(self):
        return public_stadiums().prefetch_related('fields__time_slots')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        occupied_slot_ids = Reservation.objects.filter(
            status__in=Reservation.occupying_statuses(),
        ).values_list('time_slot_id', flat=True)
        context['occupied_slot_ids'] = set(occupied_slot_ids)
        return context


class StadiumAdminPendingView(generics.ListAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = StadiumAuditSerializer

    def get_queryset(self):
        return pending_stadiums().order_by('created_at')


class StadiumAdminApproveView(APIView):
    permission_classes = [IsSystemAdmin]

    def post(self, request, pk):
        stadium = get_object_or_404(pending_stadiums(), pk=pk)
        result = stadium.approve()
        if result == 'deleted':
            return Response({'detail': '场馆删除申请已通过。', 'action': 'deleted'})
        return Response(StadiumAuditSerializer(stadium).data)


class StadiumAdminRejectView(APIView):
    permission_classes = [IsSystemAdmin]

    def post(self, request, pk):
        stadium = get_object_or_404(pending_stadiums(), pk=pk)
        stadium.reject()
        return Response(StadiumAuditSerializer(stadium).data)


class StadiumCommentsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CommentSerializer

    def get_queryset(self):
        stadium = get_object_or_404(public_stadiums(), pk=self.kwargs['pk'])
        return stadium.comments.filter(audit_status=CommentAuditStatus.APPROVED).select_related('user')


class ReservationCreateView(generics.CreateAPIView):
    permission_classes = [IsOrdinaryUser]
    serializer_class = ReservationCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MyReservationsView(generics.ListAPIView):
    permission_classes = [IsOrdinaryUser]
    serializer_class = ReservationSerializer

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user).select_related('time_slot__field__stadium')


def admin_reservations(user):
    return Reservation.objects.filter(
        time_slot__field__stadium__owner=user,
    ).select_related('user', 'time_slot__field__stadium')


class AdminPendingReservationsView(generics.ListAPIView):
    permission_classes = [IsStadiumAdmin]
    serializer_class = ReservationSerializer

    def get_queryset(self):
        return admin_reservations(self.request.user).filter(
            status=ReservationStatus.PENDING,
        ).order_by('created_at')


class ReservationApproveView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request, pk):
        reservation = get_object_or_404(
            admin_reservations(request.user),
            pk=pk,
            status=ReservationStatus.PENDING,
        )
        try:
            reservation.approve()
        except DjangoValidationError as exc:
            return Response({'detail': serializer_error(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ReservationSerializer(reservation).data)


class ReservationRejectView(APIView):
    permission_classes = [IsStadiumAdmin]

    def post(self, request, pk):
        reservation = get_object_or_404(
            admin_reservations(request.user),
            pk=pk,
            status=ReservationStatus.PENDING,
        )
        reservation.reject()
        return Response(ReservationSerializer(reservation).data)


class ReservationCancelView(APIView):
    permission_classes = [IsOrdinaryUser]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
        try:
            reservation.cancel()
        except DjangoValidationError as exc:
            return Response({'detail': serializer_error(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ReservationSerializer(reservation).data)


class CommentCreateView(generics.CreateAPIView):
    permission_classes = [IsOrdinaryUser]
    serializer_class = CommentCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MyCommentsView(generics.ListAPIView):
    permission_classes = [IsOrdinaryUser]
    serializer_class = CommentSerializer

    def get_queryset(self):
        return (
            Comment.objects.filter(user=self.request.user)
            .select_related('user', 'stadium')
            .order_by('-created_at')
        )


class MyCommentDeleteView(APIView):
    permission_classes = [IsOrdinaryUser]

    def delete(self, request, pk):
        comment = get_object_or_404(Comment.objects.all(), pk=pk, user=request.user)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentAdminPendingView(generics.ListAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = CommentSerializer

    def get_queryset(self):
        return (
            Comment.objects.filter(audit_status=CommentAuditStatus.PENDING)
            .select_related('user', 'stadium')
            .order_by('created_at')
        )


class CommentAdminApproveView(APIView):
    permission_classes = [IsSystemAdmin]

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, audit_status=CommentAuditStatus.PENDING)
        comment.approve()
        return Response(CommentSerializer(comment).data)


class CommentAdminRejectView(APIView):
    permission_classes = [IsSystemAdmin]

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, audit_status=CommentAuditStatus.PENDING)
        comment.reject()
        return Response(CommentSerializer(comment).data)


class CommentAdminDeleteView(APIView):
    permission_classes = [IsSystemAdmin]

    def delete(self, request, pk):
        comment = get_object_or_404(Comment.objects.all(), pk=pk)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

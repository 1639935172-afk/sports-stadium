from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from comments.models import Comment, CommentAuditStatus
from reservations.models import Reservation
from stadiums.models import Stadium, StadiumAuditStatus

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
    StadiumDetailSerializer,
    StadiumListSerializer,
    UserSerializer,
)


class IsOrdinaryUser(permissions.BasePermission):
    message = '只有普通用户可以执行该操作。'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ORDINARY)


def public_stadiums():
    return Stadium.objects.filter(
        audit_status=StadiumAuditStatus.APPROVED,
        is_open=True,
        deletion_requested=False,
    )


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

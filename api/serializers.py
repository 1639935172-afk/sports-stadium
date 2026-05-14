from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserRole
from comments.models import Comment, CommentAuditStatus
from reservations.models import Reservation
from stadiums.models import Field, Stadium, StadiumAuditStatus, TimeSlot


class ApiValidationMixin:
    def _raise_serializer_error(self, exc):
        if hasattr(exc, 'message_dict'):
            raise serializers.ValidationError(exc.message_dict)
        if hasattr(exc, 'messages'):
            raise serializers.ValidationError(exc.messages)
        raise serializers.ValidationError(str(exc))


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'phone_number', 'nickname', 'role', 'is_active', 'is_cancelled']
        read_only_fields = fields


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['nickname']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('当前密码错误')
        return value

    def validate_new_password1(self, value):
        validate_password(value, self.context['request'].user)
        return value

    def validate(self, attrs):
        if attrs.get('new_password1') != attrs.get('new_password2'):
            raise serializers.ValidationError({'new_password2': '两次输入的新密码不一致'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save(update_fields=['password'])
        return user


class PasswordResetSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    verification_code = serializers.CharField(max_length=6)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        phone_number = value.strip()
        try:
            self.user = get_user_model().objects.get(phone_number=phone_number, is_cancelled=False)
        except get_user_model().DoesNotExist as exc:
            raise serializers.ValidationError('该手机号未注册') from exc
        return phone_number

    def validate_verification_code(self, value):
        if value.strip() != '123456':
            raise serializers.ValidationError('验证码错误')
        return value.strip()

    def validate_new_password1(self, value):
        validate_password(value, getattr(self, 'user', None))
        return value

    def validate(self, attrs):
        if attrs.get('new_password1') != attrs.get('new_password2'):
            raise serializers.ValidationError({'new_password2': '两次输入的新密码不一致'})
        return attrs

    def save(self, **kwargs):
        user = self.user
        user.set_password(self.validated_data['new_password1'])
        user.is_active = True
        user.save(update_fields=['password', 'is_active'])
        return user


class AccountCancelSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('密码不正确')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.cancel_account()
        return user


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    verification_code = serializers.CharField(max_length=6, write_only=True)

    def validate_phone_number(self, value):
        phone_number = value.strip()
        if not phone_number.isdigit() or len(phone_number) != 11:
            raise serializers.ValidationError('手机号必须是11位数字')
        if get_user_model().objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError('该手机号已注册')
        return phone_number

    def validate_password1(self, value):
        validate_password(value)
        return value

    def validate_verification_code(self, value):
        if value.strip() != '123456':
            raise serializers.ValidationError('验证码错误')
        return value.strip()

    def validate(self, attrs):
        if attrs.get('password1') != attrs.get('password2'):
            raise serializers.ValidationError({'password2': '两次输入的密码不一致'})
        return attrs

    def create(self, validated_data):
        return get_user_model().objects.create_user(
            phone_number=validated_data['phone_number'],
            password=validated_data['password1'],
            nickname=validated_data.get('nickname', ''),
            role=UserRole.ORDINARY,
        )


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = authenticate(request, username=attrs.get('phone_number'), password=attrs.get('password'))
        if user is None or not user.can_login:
            raise serializers.ValidationError('手机号或密码错误')
        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        user = instance['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        }


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'date', 'start_time', 'end_time', 'is_available']
        read_only_fields = fields


class FieldSerializer(serializers.ModelSerializer):
    time_slots = serializers.SerializerMethodField()

    class Meta:
        model = Field
        fields = ['id', 'field_type', 'number', 'price_per_hour', 'time_slots']
        read_only_fields = fields

    def get_time_slots(self, obj):
        occupied_slot_ids = self.context.get('occupied_slot_ids', set())
        slots = obj.time_slots.filter(is_available=True).exclude(id__in=occupied_slot_ids)
        return TimeSlotSerializer(slots, many=True).data


class StadiumListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stadium
        fields = ['id', 'name', 'address', 'phone_number', 'information']
        read_only_fields = fields


class StadiumDetailSerializer(serializers.ModelSerializer):
    fields = serializers.SerializerMethodField(method_name='get_stadium_fields')

    class Meta:
        model = Stadium
        fields = ['id', 'name', 'address', 'phone_number', 'information', 'fields']
        read_only_fields = fields

    def get_stadium_fields(self, obj):
        fields = obj.fields.filter(is_active=True).prefetch_related('time_slots')
        return FieldSerializer(fields, many=True, context=self.context).data


class CommentSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'stadium', 'user_nickname', 'content', 'audit_status', 'created_at']
        read_only_fields = ['id', 'user_nickname', 'audit_status', 'created_at']


class CommentCreateSerializer(ApiValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'stadium', 'content', 'audit_status', 'created_at']
        read_only_fields = ['id', 'audit_status', 'created_at']

    def create(self, validated_data):
        comment = Comment(user=self.context['request'].user, **validated_data)
        try:
            comment.save()
        except DjangoValidationError as exc:
            self._raise_serializer_error(exc)
        return comment


class ReservationSerializer(serializers.ModelSerializer):
    stadium_name = serializers.CharField(source='time_slot.field.stadium.name', read_only=True)
    field_number = serializers.CharField(source='time_slot.field.number', read_only=True)
    field_type = serializers.CharField(source='time_slot.field.field_type', read_only=True)
    date = serializers.DateField(source='time_slot.date', read_only=True)
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='time_slot.end_time', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'time_slot', 'status', 'stadium_name', 'field_number', 'field_type',
            'date', 'start_time', 'end_time', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class ReservationCreateSerializer(ApiValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'time_slot', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    def create(self, validated_data):
        reservation = Reservation(user=self.context['request'].user, **validated_data)
        try:
            reservation.save()
        except DjangoValidationError as exc:
            self._raise_serializer_error(exc)
        return reservation

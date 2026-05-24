from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone
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


class SystemUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['nickname', 'role', 'is_active', 'is_cancelled']

    def validate(self, attrs):
        is_cancelled = attrs.get('is_cancelled')
        is_active = attrs.get('is_active')
        if is_cancelled is True:
            attrs['is_active'] = False
        elif is_cancelled is False and is_active is None and self.instance and not self.instance.is_active:
            attrs['is_active'] = self.instance.is_active
        return attrs

    def save(self, **kwargs):
        user = super().save(**kwargs)
        if user.is_cancelled and user.is_active:
            user.is_active = False
            user.save(update_fields=['is_active'])
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
        # App 登录后需要这两个 token：access 放请求头，refresh 预留给续期。
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


class TimeSlotManageSerializer(ApiValidationMixin, serializers.ModelSerializer):
    field_number = serializers.CharField(source='field.number', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)
    stadium_name = serializers.CharField(source='field.stadium.name', read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            'id',
            'field',
            'field_number',
            'field_type',
            'stadium_name',
            'date',
            'start_time',
            'end_time',
            'is_available',
        ]
        read_only_fields = ['id', 'field', 'field_number', 'field_type', 'stadium_name']

    def create(self, validated_data):
        time_slot = TimeSlot(**validated_data)
        try:
            time_slot.save()
        except DjangoValidationError as exc:
            self._raise_serializer_error(exc)
        return time_slot

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            instance.save()
        except DjangoValidationError as exc:
            self._raise_serializer_error(exc)
        return instance


class TimeSlotBulkGenerateSerializer(serializers.Serializer):
    field_scope = serializers.ChoiceField(choices=['current', 'all'], default='current')
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    slot_minutes = serializers.IntegerField(min_value=15, max_value=240)
    price_per_hour = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    is_available = serializers.BooleanField(default=True)
    skip_existing = serializers.BooleanField(default=True)

    def validate_start_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError('开始日期不能早于今天')
        return value

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError({'end_date': '结束日期不能早于开始日期'})
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError({'end_time': '每日结束时间必须晚于开始时间'})
        return attrs


class FieldSerializer(serializers.ModelSerializer):
    time_slots = serializers.SerializerMethodField()

    class Meta:
        model = Field
        fields = ['id', 'field_type', 'number', 'price_per_hour', 'time_slots']
        read_only_fields = fields

    def get_time_slots(self, obj):
        # 场馆详情 API 在这里过滤掉不可用、已占用、已过期的时段，
        # 所以 App 端展示的 time_slots 默认就是可预约时段。
        occupied_slot_ids = self.context.get('occupied_slot_ids', set())
        now = self.context.get('now')
        slots = obj.time_slots.filter(is_available=True).exclude(id__in=occupied_slot_ids)
        if now is not None:
            slots = slots.filter(Q(date__gt=now.date()) | Q(date=now.date(), start_time__gt=now.time()))
        return TimeSlotSerializer(slots, many=True).data


class FieldManageSerializer(ApiValidationMixin, serializers.ModelSerializer):
    stadium_name = serializers.CharField(source='stadium.name', read_only=True)

    class Meta:
        model = Field
        fields = [
            'id',
            'stadium',
            'stadium_name',
            'field_type',
            'number',
            'is_active',
            'price_per_hour',
        ]
        read_only_fields = ['id', 'stadium', 'stadium_name']


class StadiumCoverImageSerializerMixin:
    def get_cover_image_url(self, obj):
        if not obj.cover_image:
            return ''
        url = obj.cover_image.url
        request = self.context.get('request')
        if request is None:
            return url
        return request.build_absolute_uri(url)


class StadiumListSerializer(StadiumCoverImageSerializerMixin, serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Stadium
        fields = [
            'id',
            'name',
            'address',
            'phone_number',
            'information',
            'cover_image_url',
            'audit_status',
            'is_open',
            'deletion_requested',
        ]
        read_only_fields = fields


class StadiumAuditSerializer(StadiumCoverImageSerializerMixin, serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    owner_nickname = serializers.CharField(source='owner.nickname', read_only=True)
    owner_phone_number = serializers.CharField(source='owner.phone_number', read_only=True)

    class Meta:
        model = Stadium
        fields = [
            'id',
            'name',
            'address',
            'phone_number',
            'information',
            'cover_image_url',
            'audit_status',
            'is_open',
            'deletion_requested',
            'owner_nickname',
            'owner_phone_number',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class StadiumManageSerializer(StadiumCoverImageSerializerMixin, serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Stadium
        fields = [
            'id',
            'name',
            'address',
            'phone_number',
            'information',
            'cover_image_url',
            'audit_status',
            'is_open',
            'deletion_requested',
        ]
        read_only_fields = ['id', 'cover_image_url', 'audit_status', 'is_open', 'deletion_requested']


class StadiumDetailSerializer(StadiumCoverImageSerializerMixin, serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    fields = serializers.SerializerMethodField(method_name='get_stadium_fields')

    class Meta:
        model = Stadium
        fields = ['id', 'name', 'address', 'phone_number', 'information', 'cover_image_url', 'fields']
        read_only_fields = fields

    def get_stadium_fields(self, obj):
        fields = obj.fields.filter(is_active=True).prefetch_related('time_slots')
        return FieldSerializer(fields, many=True, context=self.context).data


class CommentSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    user_phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    stadium_name = serializers.CharField(source='stadium.name', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'stadium', 'stadium_name', 'user_nickname', 'user_phone_number',
            'content', 'audit_status', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'stadium_name', 'user_nickname', 'user_phone_number', 'audit_status', 'created_at']


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
    is_expired = serializers.BooleanField(read_only=True)
    payment_status = serializers.SerializerMethodField()
    payment_amount = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'time_slot', 'status', 'stadium_name', 'field_number', 'field_type',
            'date', 'start_time', 'end_time', 'is_expired', 'payment_status',
            'payment_amount', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_payment_status(self, obj):
        if not hasattr(obj, 'payment'):
            return ''
        return obj.payment.status

    def get_payment_amount(self, obj):
        if not hasattr(obj, 'payment'):
            return ''
        return str(obj.payment.amount)


class ReservationCreateSerializer(ApiValidationMixin, serializers.ModelSerializer):
    payment_status = serializers.SerializerMethodField()
    payment_amount = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = ['id', 'time_slot', 'status', 'payment_status', 'payment_amount', 'created_at']
        read_only_fields = ['id', 'status', 'payment_status', 'payment_amount', 'created_at']

    def get_payment_status(self, obj):
        if not hasattr(obj, 'payment'):
            return ''
        return obj.payment.status

    def get_payment_amount(self, obj):
        if not hasattr(obj, 'payment'):
            return ''
        return str(obj.payment.amount)

    def create(self, validated_data):
        # App 只提交 time_slot；用户来自 request.user，支付单由 ensure_payment() 自动生成。
        reservation = Reservation(user=self.context['request'].user, **validated_data)
        try:
            reservation.save()
            reservation.ensure_payment()
        except DjangoValidationError as exc:
            self._raise_serializer_error(exc)
        return reservation

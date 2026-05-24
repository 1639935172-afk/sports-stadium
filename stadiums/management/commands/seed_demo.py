from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserRole
from comments.models import Comment, CommentAuditStatus
from reservations.models import Reservation, ReservationStatus
from stadiums.models import Field, Stadium, StadiumAuditStatus, TimeSlot


class Command(BaseCommand):
    help = 'Create a repeatable demo dataset for the stadium reservation workflow.'

    def handle(self, *args, **options):
        User = get_user_model()

        system_admin, _ = User.objects.update_or_create(
            phone_number='18800000001',
            defaults={
                'nickname': '系统管理员演示号',
                'role': UserRole.SYSTEM_ADMIN,
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
                'is_cancelled': False,
            },
        )
        system_admin.set_password('DemoPass123')
        system_admin.save()

        stadium_admin, _ = User.objects.update_or_create(
            phone_number='18800000002',
            defaults={
                'nickname': '场馆管理员演示号',
                'role': UserRole.STADIUM_ADMIN,
                'is_active': True,
                'is_cancelled': False,
            },
        )
        stadium_admin.set_password('DemoPass123')
        stadium_admin.save()

        ordinary_user, _ = User.objects.update_or_create(
            phone_number='18800000003',
            defaults={
                'nickname': '普通用户演示号',
                'role': UserRole.ORDINARY,
                'is_active': True,
                'is_cancelled': False,
            },
        )
        ordinary_user.set_password('DemoPass123')
        ordinary_user.save()

        stadium, _ = Stadium.objects.update_or_create(
            owner=stadium_admin,
            name='演示综合体育馆',
            defaults={
                'address': '演示市中心路 88 号',
                'phone_number': '13812345678',
                'information': '用于演示场馆提交、审核、预约、评论的完整主流程。',
                'audit_status': StadiumAuditStatus.APPROVED,
                'is_open': True,
                'deletion_requested': False,
            },
        )

        field, _ = Field.objects.update_or_create(
            stadium=stadium,
            number='A1',
            defaults={
                'field_type': '篮球场',
                'is_active': True,
                'price_per_hour': Decimal('80.00'),
            },
        )

        slot, _ = TimeSlot.objects.update_or_create(
            field=field,
            date=date(2026, 6, 8),
            start_time=time(9, 0),
            defaults={
                'end_time': time(10, 0),
                'is_available': True,
            },
        )

        reservation, _ = Reservation.objects.update_or_create(
            user=ordinary_user,
            time_slot=slot,
            defaults={'status': ReservationStatus.PENDING},
        )
        payment = reservation.ensure_payment()
        if payment.status == 'unpaid':
            payment.mark_paid()

        Comment.objects.update_or_create(
            user=ordinary_user,
            stadium=stadium,
            content='场馆环境不错，预约流程清晰。',
            defaults={'audit_status': CommentAuditStatus.APPROVED},
        )
        Comment.objects.update_or_create(
            user=ordinary_user,
            stadium=stadium,
            content='这条评论用于演示系统管理员审核。',
            defaults={'audit_status': CommentAuditStatus.PENDING},
        )

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write('System admin: 18800000001 / DemoPass123')
        self.stdout.write('Stadium admin: 18800000002 / DemoPass123')
        self.stdout.write('Ordinary user: 18800000003 / DemoPass123')
        self.stdout.write(f'Pending reservation id: {reservation.pk}')

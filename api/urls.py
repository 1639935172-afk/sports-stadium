from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    # App 端请求的完整地址 = Flutter ApiClient.baseUrl + 这里的 path。
    # 例如 baseUrl 是 http://10.0.2.2:8000/api，登录接口就是 /auth/login/。
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('account/cancel/', views.AccountCancelView.as_view(), name='account_cancel'),
    path('system/users/', views.SystemUserListView.as_view(), name='system_user_list'),
    path('system/users/<int:pk>/', views.SystemUserDetailView.as_view(), name='system_user_detail'),
    path('stadiums/', views.StadiumListView.as_view(), name='stadium_list'),
    path('stadiums/admin/pending/', views.StadiumAdminPendingView.as_view(), name='stadium_admin_pending'),
    path('stadiums/mine/', views.StadiumMineView.as_view(), name='stadium_mine'),
    path('stadiums/mine/<int:pk>/', views.StadiumMineDetailView.as_view(), name='stadium_mine_detail'),
    path('stadiums/mine/<int:pk>/delete-request/', views.StadiumMineDeleteRequestView.as_view(), name='stadium_mine_delete_request'),
    path('stadiums/mine/<int:stadium_pk>/fields/', views.FieldManageListCreateView.as_view(), name='field_manage_list_create'),
    path('fields/<int:field_pk>/time-slots/', views.TimeSlotManageListCreateView.as_view(), name='time_slot_manage_list_create'),
    path('fields/<int:field_pk>/time-slots/generate/', views.TimeSlotBulkGenerateView.as_view(), name='time_slot_bulk_generate'),
    path('fields/<int:field_pk>/time-slots/clear-expired/', views.TimeSlotClearExpiredView.as_view(), name='time_slot_clear_expired'),
    path('fields/<int:pk>/', views.FieldManageDetailView.as_view(), name='field_manage_detail'),
    path('fields/<int:pk>/disable/', views.FieldDisableView.as_view(), name='field_disable'),
    path('time-slots/<int:pk>/', views.TimeSlotManageDetailView.as_view(), name='time_slot_manage_detail'),
    path('stadiums/<int:pk>/', views.StadiumDetailView.as_view(), name='stadium_detail'),
    path('stadiums/<int:pk>/approve/', views.StadiumAdminApproveView.as_view(), name='stadium_admin_approve'),
    path('stadiums/<int:pk>/reject/', views.StadiumAdminRejectView.as_view(), name='stadium_admin_reject'),
    path('stadiums/<int:pk>/comments/', views.StadiumCommentsView.as_view(), name='stadium_comments'),
    path('reservations/', views.ReservationCreateView.as_view(), name='reservation_create'),
    path('reservations/mine/', views.MyReservationsView.as_view(), name='my_reservations'),
    path('reservations/admin/pending/', views.AdminPendingReservationsView.as_view(), name='admin_pending_reservations'),
    path('reservations/<int:pk>/pay/', views.ReservationPayView.as_view(), name='reservation_pay'),
    path('reservations/<int:pk>/payment-fail/', views.ReservationPaymentFailView.as_view(), name='reservation_payment_fail'),
    path('reservations/<int:pk>/approve/', views.ReservationApproveView.as_view(), name='reservation_approve'),
    path('reservations/<int:pk>/reject/', views.ReservationRejectView.as_view(), name='reservation_reject'),
    path('reservations/<int:pk>/cancel/', views.ReservationCancelView.as_view(), name='reservation_cancel'),
    path('comments/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comments/mine/', views.MyCommentsView.as_view(), name='my_comments'),
    path('comments/mine/<int:pk>/', views.MyCommentDeleteView.as_view(), name='my_comment_delete'),
    path('comments/admin/pending/', views.CommentAdminPendingView.as_view(), name='comment_admin_pending'),
    path('comments/<int:pk>/approve/', views.CommentAdminApproveView.as_view(), name='comment_admin_approve'),
    path('comments/<int:pk>/reject/', views.CommentAdminRejectView.as_view(), name='comment_admin_reject'),
    path('comments/<int:pk>/', views.CommentAdminDeleteView.as_view(), name='comment_admin_delete'),
]

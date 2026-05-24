from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('admin/pending/', views.admin_pending_reservations_view, name='admin_pending'),
    path('mine/', views.my_reservations_view, name='mine'),
    path('<int:pk>/pay/', views.reservation_pay_view, name='pay'),
    path('<int:pk>/payment-fail/', views.reservation_payment_fail_view, name='payment_fail'),
    path('<int:pk>/approve/', views.reservation_approve_view, name='approve'),
    path('<int:pk>/reject/', views.reservation_reject_view, name='reject'),
    path('<int:pk>/cancel/', views.reservation_cancel_view, name='cancel'),
    path('slots/<int:slot_pk>/book/', views.reservation_create_view, name='create'),
]

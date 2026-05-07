from django.urls import path

from . import views

app_name = 'stadiums'

urlpatterns = [
    path('', views.stadium_list_view, name='list'),
    path('mine/', views.my_stadiums_view, name='my_stadiums'),
    path('new/', views.stadium_create_view, name='create'),
    path('<int:stadium_pk>/fields/', views.field_list_view, name='field_list'),
    path('<int:stadium_pk>/fields/new/', views.field_create_view, name='field_create'),
    path('fields/<int:pk>/edit/', views.field_edit_view, name='field_edit'),
    path('fields/<int:pk>/disable/', views.field_disable_view, name='field_disable'),
    path('fields/<int:pk>/delete/', views.field_delete_view, name='field_delete'),
    path('fields/<int:field_pk>/time-slots/', views.time_slot_list_view, name='time_slot_list'),
    path('fields/<int:field_pk>/time-slots/new/', views.time_slot_create_view, name='time_slot_create'),
    path('time-slots/<int:pk>/edit/', views.time_slot_edit_view, name='time_slot_edit'),
    path('time-slots/<int:pk>/delete/', views.time_slot_delete_view, name='time_slot_delete'),
    path('<int:pk>/edit/', views.stadium_edit_view, name='edit'),
    path('<int:pk>/delete-request/', views.stadium_delete_request_view, name='delete_request'),
    path('audit/', views.audit_list_view, name='audit_list'),
    path('audit/<int:pk>/approve/', views.audit_approve_view, name='audit_approve'),
    path('audit/<int:pk>/reject/', views.audit_reject_view, name='audit_reject'),
    path('<int:pk>/', views.stadium_detail_view, name='detail'),
]

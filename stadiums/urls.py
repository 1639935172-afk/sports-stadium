from django.urls import path

from . import views

app_name = 'stadiums'

urlpatterns = [
    path('', views.stadium_list_view, name='list'),
    path('mine/', views.my_stadiums_view, name='my_stadiums'),
    path('new/', views.stadium_create_view, name='create'),
    path('<int:pk>/edit/', views.stadium_edit_view, name='edit'),
    path('<int:pk>/delete-request/', views.stadium_delete_request_view, name='delete_request'),
    path('audit/', views.audit_list_view, name='audit_list'),
    path('audit/<int:pk>/approve/', views.audit_approve_view, name='audit_approve'),
    path('audit/<int:pk>/reject/', views.audit_reject_view, name='audit_reject'),
    path('<int:pk>/', views.stadium_detail_view, name='detail'),
]

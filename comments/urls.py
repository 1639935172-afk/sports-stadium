from django.urls import path

from . import views

app_name = 'comments'

urlpatterns = [
    path('audit/', views.comment_audit_list_view, name='audit_list'),
    path('stadiums/<int:stadium_pk>/new/', views.comment_create_view, name='create'),
    path('<int:pk>/approve/', views.comment_approve_view, name='approve'),
    path('<int:pk>/reject/', views.comment_reject_view, name='reject'),
    path('<int:pk>/delete/', views.comment_delete_view, name='delete'),
]

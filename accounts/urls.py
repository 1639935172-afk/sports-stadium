from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('system/users/', views.system_user_list_view, name='system_user_list'),
    path('system/users/<int:pk>/edit/', views.system_user_edit_view, name='system_user_edit'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password/change/', views.password_change_view, name='password_change'),
    path('password/reset/', views.password_reset_view, name='password_reset'),
    path('cancel/', views.account_cancel_view, name='account_cancel'),
]


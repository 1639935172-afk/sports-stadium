from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('account/cancel/', views.AccountCancelView.as_view(), name='account_cancel'),
    path('stadiums/', views.StadiumListView.as_view(), name='stadium_list'),
    path('stadiums/<int:pk>/', views.StadiumDetailView.as_view(), name='stadium_detail'),
    path('stadiums/<int:pk>/comments/', views.StadiumCommentsView.as_view(), name='stadium_comments'),
    path('reservations/', views.ReservationCreateView.as_view(), name='reservation_create'),
    path('reservations/mine/', views.MyReservationsView.as_view(), name='my_reservations'),
    path('reservations/<int:pk>/cancel/', views.ReservationCancelView.as_view(), name='reservation_cancel'),
    path('comments/', views.CommentCreateView.as_view(), name='comment_create'),
]

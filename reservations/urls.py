from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('mine/', views.my_reservations_view, name='mine'),
    path('slots/<int:slot_pk>/book/', views.reservation_create_view, name='create'),
]

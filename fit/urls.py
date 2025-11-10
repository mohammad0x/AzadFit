from django.urls import path
from . import views

app_name = 'fit'

urlpatterns = [
    path('register/', views.verify_login_phone, name='register'),
    path('login/', views.login_phone, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('home/' , views.home , name='home'),

    path('', views.gym_list, name='gym_list'),
    path('gym/<slug:slug>/', views.gym_detail, name='gym_detail'),

    path('timeslots/', views.timeslot_list, name='timeslot_list'),
    path('reserve/<int:timeslot_id>/<int:gym_id>/', views.reserve_time, name='reserve_time'),
    path('my-reservations/', views.user_reservations, name='user_reservations'),

    path('pay/<int:reservation_id>/', views.make_payment, name='make_payment'),
]

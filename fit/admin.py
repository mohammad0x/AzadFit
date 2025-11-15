from django.contrib import admin
from .models import *


# Register your models here.
class adminUser(admin.ModelAdmin):
    list_display = ('phone',)
    list_filter = ('is_admin', 'is_active', 'last_login')
    search_fields = ('phone',)


admin.site.register(MyUser, adminUser)


class adminGym(admin.ModelAdmin):
    list_display = ('name', 'slug', 'address', 'price', 'created_jalali')
    list_filter = ('created_jalali',)
    search_fields = ('name', 'price')


admin.site.register(Gym, adminGym)


class adminTimeSlot(admin.ModelAdmin):
    list_display = ('day_of_week', 'is_available', 'date')
    list_filter = ('day_of_week', 'date')
    search_fields = ('day_of_week',)


admin.site.register(TimeSlot, adminTimeSlot)


class adminReservation(admin.ModelAdmin):
    list_display = ('created_jalali', 'is_pey')
    list_filter = ('created_jalali', 'is_pey')


admin.site.register(Reservation, adminReservation)
admin.site.register(Image)
admin.site.register(Payment)

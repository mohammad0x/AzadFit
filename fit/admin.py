from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(MyUser)
admin.site.register(Gym)
admin.site.register(TimeSlot)
admin.site.register(Reservation)
admin.site.register(Image)
from django.contrib.auth.backends import BaseBackend
from .models import MyUser

class PhoneNumberBackend(BaseBackend):
    def authenticate(self, request, phone=None):
        if request and request.path.startswith('/admin'):
            return None

        try:
            user = MyUser.objects.get(phone=phone)
            return user if user.is_active else None
        except MyUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return MyUser.objects.get(pk=user_id)
        except MyUser.DoesNotExist:
            return None
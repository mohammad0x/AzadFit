from django import forms
from .models import *


class CodePhoneForm(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = ['verify_code']

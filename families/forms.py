from django import forms
from .models import Family

class FamilyProfileForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ("name", "image_url")
        labels = {
            "name": "苗字（家族名）",
            "image_url": "家族アイコン",
        }
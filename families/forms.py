from django import forms
from .models import Family

class FamilyProfileForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ("name", "image")
        labels = {
            "name": "苗字（家族名）",
            "image": "家族アイコン",
        }
        # Django のデフォルトだと ClearableFileInput になりやすく、画面上でCurrently、Change、Clearのような表示が出てしまう
        # forms.FileInput()にするとそれらのUIを出さずにできる
        widgets = {
            "image": forms.FileInput(), 
        }
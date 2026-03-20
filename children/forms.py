# children/forms.py
from django import forms
from .models import Child

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ["name", "image"]
        labels = {
            "name": "子ども名",
            "image": "子どもアイコン",
        }
        widgets = {
            "image": forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 編集時に画像未選択でも、既存画像をそのまま維持できるようにする
        if self.instance and self.instance.pk:
            self.fields["image"].required = False
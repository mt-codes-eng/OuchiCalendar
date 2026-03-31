# children/forms.py
from django import forms
from .models import Child

from color_assignments.constants import COLOR_HEX_MAP
from color_assignments.models import FamilyColorAssignment

class ChildForm(forms.ModelForm):
    color_code = forms.ChoiceField(
        label="個人カラー",
        required=True,
    )
    
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
        
         # 個人カラーの選択肢を作る
        self.fields["color_code"].choices = [
            ("", "選択してください"),
            *[(code, hex_color) for code, hex_color in COLOR_HEX_MAP.items()]
        ]

        # 編集時に画像未選択でも、既存画像をそのまま維持できるようにする
        if self.instance and self.instance.pk:
            self.fields["image"].required = False
            
             # 既存の子どもカラーがあれば、初期値として入れる
            assignment = FamilyColorAssignment.objects.filter(
                child=self.instance
            ).first()

            if assignment:
                self.fields["color_code"].initial = str(assignment.color_code)

    def clean_color_code(self):
        """
        個人カラー欄専用の入力チェック

        ChoiceField は送信時に文字列になることがあるので、
        int に変換して返す
        """
        color_code = self.cleaned_data.get("color_code")

        # 未選択チェック
        if color_code in [None, ""]:
            raise forms.ValidationError("個人カラーを選択してください")

        # 文字列 → int に変換
        try:
            color_code = int(color_code)
        except (TypeError, ValueError):
            raise forms.ValidationError("個人カラーの値が不正です")

        # 13色パレットの中か確認
        if color_code not in COLOR_HEX_MAP:
            raise forms.ValidationError("選択できない色です")

        return color_code
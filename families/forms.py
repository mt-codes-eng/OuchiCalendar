from django import forms
from .models import Family

from color_assignments.constants import COLOR_HEX_MAP
from color_assignments.models import FamilyColorAssignment

class FamilyProfileForm(forms.ModelForm):
    # 合同予定カラー選択欄
    color_code = forms.ChoiceField(
        label="合同予定カラー",
        required=True,
    )
    
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
        
    def __init__(self, *args, **kwargs):
        """
        フォーム生成時の初期設定
        """
        super().__init__(*args, **kwargs)

        # 合同予定カラーの選択肢を作る
        # 例: ("0", "#ff7f7f"), ("1", "#ff7fbf"), ...
        self.fields["color_code"].choices = [
            ("", "選択してください"),
            *[(code, hex_color) for code, hex_color in COLOR_HEX_MAP.items()]
        ]

        # 編集中の family に、すでに合同予定カラーがあるなら
        # 初期値としてフォームに入れておく
        if self.instance and self.instance.pk:
            assignment = FamilyColorAssignment.objects.filter(
                family=self.instance,
                assign_type=FamilyColorAssignment.AssignType.SHARED,
            ).first()

            if assignment:
                self.fields["color_code"].initial = str(assignment.color_code)

    def clean_color_code(self):
        """
        合同予定カラー欄専用の入力チェック

        ChoiceField は送信時に文字列になることがあるので、
        int に変換して返す
        """
        color_code = self.cleaned_data.get("color_code")

        # 未選択チェック
        if color_code in [None, ""]:
            raise forms.ValidationError("合同予定カラーを選択してください")

        # 文字列 → int に変換
        try:
            color_code = int(color_code)
        except (TypeError, ValueError):
            raise forms.ValidationError("合同予定カラーの値が不正です")

        # 13色パレットの中か確認
        if color_code not in COLOR_HEX_MAP:
            raise forms.ValidationError("選択できない色です")

        return color_code
from django import forms

from .models import BowelMovementRecord, AbsenceRecord


class BowelMovementRecordForm(forms.ModelForm):
    """
    排便記録フォーム

    画面で入力する項目
    - 排便があったか
    - メモ
    - 気になることがあるか
    - 気になることメモ

    child と record_date は画面で入力させず、
    view 側でセットする想定
    """

    class Meta:
        model = BowelMovementRecord

        # child / record_date は入れない
        # → view 側で自動セットするため
        fields = [
            "has_bowel_movement",
            "memo",
            "has_concern",
            "concern_memo",
        ]

        labels = {
            "has_bowel_movement": "排便があった",
            "memo": "メモ",
            "has_concern": "気になることがある",
            "concern_memo": "メモ",
        }

        widgets = {
            "memo": forms.Textarea(
                attrs={
                    "rows": 1,
                    "placeholder": "メモ（硬さなど）",
                }
            ),
            "concern_memo": forms.Textarea(
                attrs={
                    "rows": 1,
                    "placeholder": "メモ（今日は出ていないなど）",
                }
            ),
        }


class AbsenceRecordForm(forms.ModelForm):
    """
    欠席記録フォーム

    画面で入力する項目
    - 欠席したか
    - メモ

    child と record_date は画面で入力させず、
    view 側でセットする想定
    """

    class Meta:
        model = AbsenceRecord

        # child / record_date は入れない
        # → view 側で自動セットするため
        fields = [
            "is_absent",
            "memo",
        ]

        labels = {
            "is_absent": "欠席した",
            "memo": "メモ",
        }

        widgets = {
            "memo": forms.Textarea(
                attrs={
                    "rows": 1,
                    "placeholder": "メモ（発熱のためなど）",
                }
            ),
        }
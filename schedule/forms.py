from datetime import datetime, time, timedelta
from django import forms
from django.utils import timezone
from .models import Schedule

class ScheduleFrom(forms.ModelForm):
    """
    予定の作成/編集フォーム
    - 条件付き必須（調整ONなら必須など）は clean() で判定する
    - 終日ONのときは start_at/end_at を自動セットする
    """
    
    # フォームが作られた瞬間に1回だけ動く関数
    # target_dateはビューからフォームへ渡される追加情報。None はビューから「渡されなくてもOK」の意味
    def __init__(self, *args, target_date=None, **kwargs):
        super().__init__(*args, **kwargs) #「ModelFormの元々の初期化（お約束）」を呼ぶ
        self.target_date = target_date # フォームがtarget_dateを覚えて clean() で使う
        
        # pkがない（新規作成）のとき画面上のステータスの初期表示を△調整中にする
        if not self.instance.pk:
            self.fields["status"].initial = Schedule.Status.ADJUSTING
    
    # どのモデルの、どの項目をフォームに出すか。フォームに表示するフィールドはこのリストのものだけ        
    class Meta:
        model = Schedule
        fields = [
            "title",
            "memo",
            "is_all_day",
            "start_at",
            "end_at",
            "requires_coordination",
            "coordination_type",
            "coordination_other_detail",
            "user",
            "status",
            "is_consecutive_coordination",
            "coordination_end_date",
        ]
    
    # POST送信されたあとに自動で呼ばれるチェック関数。clenメソッドで複数のフィールドのバリデーションチェック  
    def clean(self):
        # 親クラスのcleanを呼び出す。cleaned は辞書。cleaned["title"]、cleaned["start_at"]というような入力された値が入っている
        cleaned = super().clean()
        # 値を取り出して変数に入れている
        is_all_day = cleaned.get("is_all_day")
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")

        requires = cleaned.get("requires_coordination")
        coordination_type = cleaned.get("coordination_type")
        other_detail = cleaned.get("coordination_other_detail")
        user = cleaned.get("user")
        status = cleaned.get("status")
        is_consecutive = cleaned.get("is_consecutive_coordination")
        end_date = cleaned.get("coordination_end_date")

        # --- 終日ONなら start_at/end_at を自動セット ---
        # 自動セットするためには終日は「何日なのか」が必要。優先順位を作ってbase_dateを決める
        if is_all_day:
            base_date = None
            # 優先：target_date（URLやGETから渡す）
            if self.target_date:
                try:
                    base_date = datetime.strptime(self.target_date, "%Y-%m-%d").date()
                except ValueError:
                    base_date = None
            
            # 保険①：優先がなければ start_at から日付を使う
            if base_date is None and start_at:
                base_date = start_at.date()
            
            # 保険②：優先、保険①の両方なければエラー   
            if base_date is None:
                raise forms.ValidationError("終日予定のための日付が取得できません。日付を指定してください。")
            
            start_naive = datetime.combine(base_date, time.min)
            end_naive = start_naive + timedelta(days=1)

            cleaned["start_at"] = timezone.make_aware(start_naive)
            cleaned["end_at"] = timezone.make_aware(end_naive)

            start_at = cleaned["start_at"]
            end_at = cleaned["end_at"]
        
        # --- start < end の基本チェック。開始と終了が入力されているのに開始が終了より後ならダメ ---    
        if start_at and end_at and start_at >= end_at:
            self.add_error("end_at", "終了日時は開始日時より後にしてください。")

        # --- 調整OFFなら、調整系は空に寄せる（DBを綺麗に） ---
        if not requires:
            cleaned["coordination_type"] = None
            cleaned["coordination_other_detail"] = ""
            cleaned["user"] = None
            cleaned["status"] = None
            cleaned["is_consecutive_coordination"] = False
            cleaned["coordination_end_date"] = None
            return cleaned
        
        # --- 調整ONなら必須チェック ---
        if coordination_type is None:
            self.add_error("coordination_type", "対応・調整が必要な場合は対応内容を選択してください。")

        if user is None:
            self.add_error("user", "対応・調整が必要な場合は担当者（大人）を選択してください。")

        if status is None:
            self.add_error("status", "対応・調整が必要な場合はステータスを選択してください。")

        # 対応内容が「その他」なら詳細必須
        if coordination_type == Schedule.CoordinationType.OTHER and not other_detail:
            self.add_error("coordination_other_detail", "「その他」を選んだ場合は詳細を入力してください。")

        # 連続対応がONなら終了日必須
        if is_consecutive and not end_date:
            self.add_error("coordination_end_date", "連続そて対応する場合は終了日を入力してください。")

        # Djangoに「チェック済みのデータ」を返す
        return cleaned
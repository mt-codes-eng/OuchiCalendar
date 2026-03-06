from datetime import datetime, time, timedelta
from django import forms
from django.utils import timezone
from .models import Schedule

class ScheduleForm(forms.ModelForm):
    # 画面設計図に合わせて「日付」と「時間」を別フィールドで用意する（DBには保存しない）
    date = forms.DateField(
        label="日付",
        required=True, # required：入力必須
        widget=forms.DateInput(attrs={"type": "date"}) # widget：入力欄の見た目（UI）を決めるもの。カレンダーからクリックして日付を選べるようになる
    ) # attrs：HTMLの属性を追加する仕組み。attrs={"HTML属性": "値"}と書く。Pythonではattrs={"type": "date"}→HTMLでは<input type="date">となる。
    start_time = forms.TimeField(
        label="開始",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time"})
    )
    end_time = forms.TimeField(
        label="終了",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time"})
    )
    
    # どのモデルの、どの項目をフォームに出すか。フォームに表示するフィールドはこのリストのものだけ        
    class Meta:
        model = Schedule
        fields = [
            # 画面順に並べる
            "date",
            "is_all_day",
            "start_time",
            "end_time",
            "title",
            "memo",
            "requires_coordination",
            "coordination_type",
            "coordination_other_detail",
            "user",
            "status",
            "is_consecutive_coordination",
            "coordination_end_date",
        ]
        labels = {
            "is_all_day": "終日",
            "title": "予定のタイトル",
            "memo": "メモ",
            "requires_coordination": "この予定は対応・調整が必要",
            "coordination_type": "対応内容",
            "coordination_other_detail": "その他の詳細",
            "user": "担当",
            "status": "ステータス",
            "is_consecutive_coordination": "連続して対応",
            "coordination_end_date": "終了",
        }
    
    """
    予定の作成/編集フォーム
    - 条件付き必須（調整ONなら必須など）は clean() で判定する
    - 終日ONのときは start_at/end_at を自動セットする
    """
    
    # フォームが作られた瞬間に1回だけ動く関数
    # target_dateはビューからフォームへ渡される追加情報。None はビューから「渡されなくてもOK」の意味
    def __init__(self, *args, target_date=None, **kwargs):
        super().__init__(*args, **kwargs) # ModelForm本来の初期化を先に実行する。self.instanceやself.fieldsなどが使えるようになる
        self.target_date = target_date # フォームがtarget_dateを覚えて clean() で使う
        
        # 新規作成時(pkがないとき)：ステータスの初期表示を△調整中
        # instanceはこのフォームが相手にしている Schedule データ
        if not self.instance.pk:
            self.fields["status"].initial = Schedule.Status.ADJUSTING
            
        # 編集時：既存の start_at/end_at を date/start_time/end_time に分解して初期表示
        if self.instance.pk and self.instance.start_at:
            self.fields["date"].initial = self.instance.start_at.date()
            self.fields["start_time"].initial = self.instance.start_at.time().replace(second=0, microsecond=0)
            if self.instance.end_at:
                self.fields["end_time"].initial = self.instance.end_at.time().replace(second=0, microsecond=0)

        # 新規作成時でURLで ?date= を渡されたとき：「日付」の初期値に入れる
        if (not self.instance.pk) and self.target_date:
            try:
                self.fields["date"].initial = datetime.strptime(self.target_date, "%Y-%m-%d").date()
            except ValueError:
                pass

    
    # POST送信されたあとに自動で呼ばれるチェック関数。clenメソッドで複数のフィールドのバリデーションチェック  
    def clean(self):
        # 親クラスのcleanを呼び出す。cleaned は辞書。cleaned["title"]、cleaned["start_at"]というような入力された値が入っている
        cleaned = super().clean()
        
        # 画面入力（分割）
        d = cleaned.get("date")
        is_all_day = cleaned.get("is_all_day")
        start_t = cleaned.get("start_time")
        end_t = cleaned.get("end_time")
        
        # 既存項目（条件必須用）値を取り出して変数に入れている
        requires = cleaned.get("requires_coordination")
        coordination_type = cleaned.get("coordination_type")
        other_detail = cleaned.get("coordination_other_detail")
        user = cleaned.get("user")
        status = cleaned.get("status")
        is_consecutive = cleaned.get("is_consecutive_coordination")
        end_date = cleaned.get("coordination_end_date")

        # 日付が無いのはフォーム自体のエラー（ここは必須なので通常は起きない）
        if not d:
            raise forms.ValidationError("日付を選択してください。")

        # --- 終日ONなら start_at/end_at を自動セット ---
        if is_all_day:
            start_naive = datetime.combine(d, time.min)
            end_naive = start_naive + timedelta(days=1)
            cleaned["start_at"] = timezone.make_aware(start_naive)
            cleaned["end_at"] = timezone.make_aware(end_naive)
        
        # --- 終日OFF：開始・終了時刻が必要 ---   
        else:
            if not start_t:
                self.add_error("start_time", "開始時刻を入力してください。")
            if not end_t:
                self.add_error("end_time", "終了時刻を入力してください。")

            # 両方ある場合だけ start_at/end_at を作る
            if start_t and end_t:
                start_naive = datetime.combine(d, start_t)
                end_naive = datetime.combine(d, end_t)
                start_at = timezone.make_aware(start_naive)
                end_at = timezone.make_aware(end_naive)

                if start_at >= end_at:
                    self.add_error("end_time", "終了時刻は開始時刻より後にしてください。")

                cleaned["start_at"] = start_at
                cleaned["end_at"] = end_at

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
            self.add_error("coordination_end_date", "連続して対応する場合は終了日を入力してください。")

        # Djangoに「チェック済みのデータ」を返す
        return cleaned
    
    def save(self, commit=True):
        """
        分割入力（date/start_time/end_time）から start_at/end_at を作ってモデルに入れる。
        clean() で cleaned["start_at"], cleaned["end_at"] を作っている前提。
        """
        instance = super().save(commit=False)
        instance.start_at = self.cleaned_data["start_at"]
        instance.end_at = self.cleaned_data["end_at"]

        if commit:
            instance.save()
        return instance
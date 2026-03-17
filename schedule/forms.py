from datetime import datetime, time, timedelta
from django import forms
from django.utils import timezone
from django.db import transaction
from .models import Schedule, ScheduleUserMember, ScheduleChildMember
from children.models import Child
from django.contrib.auth import get_user_model

User = get_user_model()

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
    coordination_end_date = forms.DateField(
        label="終了",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    # 大人メンバーを複数選択
    user_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),   # 最初は空。__init__で家族メンバーに絞る
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="大人メンバー",
    )
    
    # 子どもメンバーを複数選択
    child_members = forms.ModelMultipleChoiceField(
        queryset=Child.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="子どもメンバー",
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
            "user_members",
            "child_members",
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
            "is_consecutive_coordination": "連続する",
        }
    
    """
    予定の作成/編集フォーム
    - 条件付き必須（調整ONなら必須など）は clean() で判定する
    - 終日ONのときは start_at/end_at を自動セットする
    """
    
    # フォームが作られた瞬間に1回だけ動く関数
    # None はビューから「渡されなくてもOK」の意味
    def __init__(self, *args, target_date=None, family=None, **kwargs):
        # ModelForm本来の初期化を先に実行する。self.instanceやself.fieldsなどが使えるようになる
        super().__init__(*args, **kwargs)
        # target_dateはビューからフォームへ渡される追加情報。フォームがtarget_dateを覚えて clean() で使う
        # target_date:カレンダー画面などから ?date=2026-03-13 のように渡された日付を新規作成時の初期値に使う
        self.target_date = target_date 
        # family:その家族に属する大人・子どもだけを予定メンバー候補として表示するために使う
        self.family = family
        
        # --- placeholder ---
        self.fields["title"].widget.attrs["placeholder"] = "タイトルを入力"
        self.fields["memo"].widget.attrs["placeholder"] = "メモを入力"
        self.fields["coordination_other_detail"].widget.attrs["placeholder"] = "詳細を入力"

        # --- Select系の先頭文言を調整 ---
        # IntegerChoicesに空選択肢を先頭追加
        self.fields["coordination_type"].choices = [
            ("", "対応内容を選択")
        ] + list(Schedule.CoordinationType.choices)
        
        self.fields["status"].choices = [
            ("", "ステータスを選択")
        ] + list(Schedule.Status.choices)

        # user は ModelChoiceField なので empty_label が使える
        self.fields["user"].empty_label = "担当者を選択"
        
        # 予定メンバーの候補を家族内に絞る
        if family:
            self.fields["user_members"].queryset = family.users.all()
            self.fields["child_members"].queryset = family.children.all()
        else:
            self.fields["user_members"].queryset = User.objects.none()
            self.fields["child_members"].queryset = Child.objects.none()
            
        # 新規作成時(pkがないとき)：ステータスの初期表示を△調整中
        # instanceはこのフォームが相手にしている Schedule データ
        if not self.instance.pk:
            self.fields["status"].initial = Schedule.Status.ADJUSTING
            
        # 編集時：既存の start_at/end_at を date/start_time/end_time に分解して初期表示
        if self.instance.pk and self.instance.start_at:
            self.fields["date"].initial = self.instance.start_at.date()

            # 終日でないときだけ時間を初期表示
            if not self.instance.is_all_day:
                self.fields["start_time"].initial = self.instance.start_at.time().replace(second=0, microsecond=0)
                if self.instance.end_at:
                    self.fields["end_time"].initial = self.instance.end_at.time().replace(second=0, microsecond=0)

        # 編集時：連続対応終了日も初期表示
        if self.instance.pk and self.instance.coordination_end_date:
            self.fields["coordination_end_date"].initial = self.instance.coordination_end_date
            
        # 新規作成時でURLで ?date= を渡されたとき：「日付」の初期値に入れる
        if (not self.instance.pk) and self.target_date:
            try:
                self.fields["date"].initial = datetime.strptime(self.target_date, "%Y-%m-%d").date()
            except ValueError:
                pass
            
        # 編集画面のとき、既存の予定メンバーにチェックを入れる
        if self.instance.pk: # self.instance.pk：編集画面かどうかの判定
            user_member_ids = []
            for membership in self.instance.user_memberships.all(): # self.instance.user_memberships.all()：この予定に紐づく中間モデル一覧を取る
                user_member_ids.append(membership.user_id)
            self.fields["user_members"].initial = user_member_ids # self.fields["user_members"].initial = [...]：フォーム表示時に最初からチェックを入れる

            child_member_ids = []
            for membership in self.instance.child_memberships.all():
                child_member_ids.append(membership.child_id)
            self.fields["child_members"].initial = child_member_ids
    
    # POST送信されたあとに自動で呼ばれるチェック関数。clenメソッドで複数のフィールドのバリデーションチェック  
    def clean(self):
        # 親クラスのcleanを呼び出す。cleaned は辞書。cleaned["title"]、cleaned["start_at"]というような入力された値が入っている
        cleaned = super().clean()
        
        # 画面入力（分割）
        d = cleaned.get("date")
        is_all_day = cleaned.get("is_all_day")
        start_t = cleaned.get("start_time")
        end_t = cleaned.get("end_time")
        
        # 調整関連
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
            raise forms.ValidationError("日付を選択してください")

        # --- 終日ON： start_at/end_at を自動セット ---
        if is_all_day:
            start_naive = datetime.combine(d, time.min)
            end_naive = start_naive + timedelta(days=1)
            cleaned["start_at"] = timezone.make_aware(start_naive)
            cleaned["end_at"] = timezone.make_aware(end_naive)
        
        # --- 終日OFF：開始・終了時刻が必要 ---   
        else:
            if not start_t:
                self.add_error("start_time", "開始時刻を入力してください")
            if not end_t:
                self.add_error("end_time", "終了時刻を入力してください")

            # 両方ある場合だけ start_at/end_at を作る
            if start_t and end_t:
                start_naive = datetime.combine(d, start_t)
                end_naive = datetime.combine(d, end_t)
                start_at = timezone.make_aware(start_naive)
                end_at = timezone.make_aware(end_naive)

                if start_at >= end_at:
                    self.add_error("end_time", "終了時刻は開始時刻より後にしてください")

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
        if not coordination_type:
            self.add_error("coordination_type", "対応・調整が必要な場合は対応内容を選択してください。")

        if not user:
            self.add_error("user", "対応・調整が必要な場合は担当者（大人）を選択してください。")

        if not status:
            self.add_error("status", "対応・調整が必要な場合はステータスを選択してください。")

        # 対応内容が「その他」なら詳細必須
        if coordination_type == Schedule.CoordinationType.OTHER and not other_detail:
            self.add_error("coordination_other_detail", "「その他」を選んだ場合は詳細を入力してください。")

        # 連続対応がONなら終了日必須
        if is_consecutive and not end_date:
            self.add_error("coordination_end_date", "連続して対応する場合は終了日を入力してください。")

        # Djangoに「チェック済みのデータ」を返す
        return cleaned
    
    # transaction.atomic を付けることで、途中で失敗したらまとめて元に戻せる
    @transaction.atomic
    def save(self, commit=True):
        """
        分割入力（date/start_time/end_time）から start_at/end_at を作ってモデルに入れる
        """
        instance = super().save(commit=False)
        # clean() で作った値をモデルに入れる
        instance.start_at = self.cleaned_data["start_at"]
        instance.end_at = self.cleaned_data["end_at"]

        if commit:
            # まず Schedule を保存
            instance.save()
            
            # 既存の予定メンバーをいったん削除
            ScheduleUserMember.objects.filter(schedule=instance).delete()
            ScheduleChildMember.objects.filter(schedule=instance).delete()
            
            # 新しい大人メンバーを保存
            user_members = self.cleaned_data.get("user_members")
            if user_members:
                ScheduleUserMember.objects.bulk_create([ # bulk_create([...])：複数データを一気にDB登録する方法
                    ScheduleUserMember(schedule=instance, user=user)
                    for user in user_members
                ])

            # 新しい子どもメンバーを保存
            child_members = self.cleaned_data.get("child_members")
            if child_members:
                ScheduleChildMember.objects.bulk_create([
                    ScheduleChildMember(schedule=instance, child=child)
                    for child in child_members
                ])

        return instance
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.utils import timezone

from children.models import Child
from .forms import BowelMovementRecordForm, AbsenceRecordForm
from .models import BowelMovementRecord, AbsenceRecord

def _parse_date(date_str: str):
    """
    URLから受け取った文字列を、Pythonで扱える date型 に変換する関数
    例："2026-05-05" → date(2026, 5, 5)
    
    date_str: str
    → 型ヒント。date_str は str型と書いているだけ。str型を強制するものではない
    
    datetime.strptime()
    →文字列を datetime型 に変換する。例:"2026-02-23"をdatetime(2026, 2, 23, 0, 0)
    
    .date()
    → datetime型 から date型 だけ取り出す。例:datetime(2026, 2, 23, 0, 0)をdate(2026, 2, 23)
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except(ValueError,TypeError):
        return None
    
@login_required
def record_create_view(request):
    """
    記録作成画面

    ・排便記録 と 欠席記録 を1画面で切り替える
    ・POSTされた record_type に応じて保存する
    
    日付の決め方
    1. URLに ?date=YYYY-MM-DD があれば、その日付
    2. なければ今日の日付
    """

    # -----------------------------
    # ① 日付
    # -----------------------------
    # URLから date を受け取る
    date_str = request.GET.get("date")
    # date_str を date型に変換
    target_date = _parse_date(date_str)
    # URLに日付がない、または不正な日付なら今日にする
    if target_date is None:
        target_date = timezone.localdate()

    # URL用の日付文字列
    date_for_url = target_date.isoformat()

    # -----------------------------
    # ② 子ども一覧を取得
    # -----------------------------
    children = Child.objects.filter(
        family=request.user.family
    ).order_by("id")

    # -----------------------------
    # ③ POST（保存処理）
    # -----------------------------
    if request.method == "POST":

        # どの記録を保存するか（radioの値）
        # "bowel" or "absence"
        
        record_type = request.POST.get("record_type")
        
        child_id = request.POST.get("child_id")
        child = get_object_or_404(
            Child,
            id=child_id,
            family=request.user.family,
        )
        
        # POSTでも日付を受け取る
        posted_date = _parse_date(request.POST.get("record_date"))
        if posted_date is None:
            posted_date = target_date

        # -------------------------
        # 排便記録の場合
        # -------------------------
        if record_type == "bowel":
            bowel_form = BowelMovementRecordForm(request.POST)
            absence_form = AbsenceRecordForm()  # 表示用だけ

            if bowel_form.is_valid():
                record = bowel_form.save(commit=False)

                # child と 日付はここでセット
                record.child = child
                record.record_date = posted_date
                record.save()

                return redirect("schedule:day", date=posted_date.isoformat())


        # -------------------------
        # 欠席記録の場合
        # -------------------------
        elif record_type == "absence":
            bowel_form = BowelMovementRecordForm()
            absence_form = AbsenceRecordForm(request.POST)

            if absence_form.is_valid():
                record = absence_form.save(commit=False)
                record.child = child
                record.record_date = posted_date
                record.save()

                return redirect("schedule:day", date=posted_date.isoformat())

    # -----------------------------
    # ④ GET（画面表示）
    # -----------------------------
    else:
        bowel_form = BowelMovementRecordForm()
        absence_form = AbsenceRecordForm()

    today = timezone.localdate()
    today_str = today.isoformat()
    
    # -----------------------------
    # ⑤ テンプレートへ渡す
    # -----------------------------
    context = {
        "bowel_form": bowel_form,
        "absence_form": absence_form,
        "date": date_for_url,
        "children": children,
        "today_str": today_str,
    }

    return render(request, "records/record_form.html", context)
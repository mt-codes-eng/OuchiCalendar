from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date

from children.models import Child
from .forms import BowelMovementRecordForm, AbsenceRecordForm
from .models import BowelMovementRecord, AbsenceRecord

@login_required
def record_create_view(request):
    """
    記録作成画面

    ・排便記録 と 欠席記録 を1画面で切り替える
    ・POSTされた record_type に応じて保存する
    """

    # -----------------------------
    # ① 日付（今回は「今日」で固定）
    # -----------------------------
    record_date = date.today()

    # -----------------------------
    # ② 子ども（今回はGETから受け取る想定）
    # 例：?child_id=1
    # -----------------------------
    child_id = request.GET.get("child_id")

    child = None
    if child_id:
        child = get_object_or_404(Child, id=child_id)

    # -----------------------------
    # ③ POST（保存処理）
    # -----------------------------
    if request.method == "POST":

        # どの記録を保存するか（radioの値）
        # "bowel" or "absence"
        record_type = request.POST.get("record_type")

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
                record.record_date = record_date

                record.save()

                return redirect("schedule:month")

        # -------------------------
        # 欠席記録の場合
        # -------------------------
        elif record_type == "absence":
            bowel_form = BowelMovementRecordForm()
            absence_form = AbsenceRecordForm(request.POST)

            if absence_form.is_valid():
                record = absence_form.save(commit=False)

                record.child = child
                record.record_date = record_date

                record.save()

                return redirect("schedule:month")

    # -----------------------------
    # ④ GET（画面表示）
    # -----------------------------
    else:
        bowel_form = BowelMovementRecordForm()
        absence_form = AbsenceRecordForm()

    # -----------------------------
    # ⑤ テンプレートへ渡す
    # -----------------------------
    context = {
        "bowel_form": bowel_form,
        "absence_form": absence_form,
        "record_date": record_date,
        "child": child,
    }

    return render(request, "records/record_form.html", context)
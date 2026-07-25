from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.utils import timezone
from django.urls import reverse

from children.models import Child
from .forms import BowelMovementRecordForm, AbsenceRecordForm
from .models import BowelMovementRecord, AbsenceRecord
from attachments.models import BowelMovementAttachment, AbsenceAttachment

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
    
def _format_japanese_date(target_date):
    """
    date型を画面表示用の文字列にする
    例：date(2026, 5, 6) → "2026/5/6（水）"
    """
    week_map = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = week_map[target_date.weekday()]
    return f"{target_date.year}/{target_date.month}/{target_date.day}（{weekday}）"    

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
    
    # 対応・調整確認ダイアログを表示するか
    show_coordination_choice = (
        request.GET.get("show_coordination_choice") == "1"
    )

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
                
                if BowelMovementRecord.objects.filter(
                    child=child,
                    record_date=posted_date,
                ).exists():
                    bowel_form.add_error(
                        None,
                        "この子どものこの日の排便記録はすでに登録されています。登録済みの記録を編集してください"
                    )
                else:
                    record.save()
                
                    # 排便記録の添付ファイルを保存する
                    for uploaded_file in request.FILES.getlist("bowel_files"):
                        BowelMovementAttachment.objects.create(
                            bowel_movement_record=record,
                            file=uploaded_file,
                            file_name=uploaded_file.name,
                        )

                    return redirect(
                        f"{reverse('records:create')}?date={posted_date.isoformat()}&show_coordination_choice=1"
                    )

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
                
                if AbsenceRecord.objects.filter(
                    child=child,
                    record_date=posted_date,
                ).exists():
                    absence_form.add_error(
                        None,
                        "この子どものこの日の欠席記録はすでに登録されています。登録済みの記録を編集してください"
                )
                else:
                    record.save()
                
                    # 欠席記録の添付ファイルを保存する
                    for uploaded_file in request.FILES.getlist("absence_files"):
                        AbsenceAttachment.objects.create(
                            absence_record=record,
                            file=uploaded_file,
                            file_name=uploaded_file.name,
                        )

                    return redirect(
                        f"{reverse('records:create')}?date={posted_date.isoformat()}&show_coordination_choice=1"
                    )
                
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
        "date": date_for_url,
        "children": children,
        "show_coordination_choice": show_coordination_choice,
    }

    return render(request, "records/record_form.html", context)

@login_required
def bowel_record_detail_view(request, pk):
    """
    排便記録の詳細画面

    URL例：
    /ouchi-calendar/records/bowel/1/

    pk は BowelMovementRecord の id
    """

    # ログイン中ユーザーの家族に属する子どもの記録だけ取得する
    # 他の家族の記録を見られないようにするため
    record = get_object_or_404(
        BowelMovementRecord.objects.select_related("child").prefetch_related("attachments"),
        pk=pk,
        child__family=request.user.family,
    )
    
    # 同じ子ども・同じ日付の欠席記録を探す
    absence_record = AbsenceRecord.objects.filter(
        child=record.child,
        record_date=record.record_date,
    ).first()

    # 日付を 2026/5/6（水）形式にする
    page_date = _format_japanese_date(record.record_date)
    day_str = record.record_date.isoformat()
    
    context = {
        "record": record,
        "record_type": "bowel",
        "page_date": page_date,
        "day_str": day_str,
        "bowel_record": record,
        "absence_record": absence_record,
    }

    return render(request, "records/record_detail.html", context)


@login_required
def absence_record_detail_view(request, pk):
    """
    欠席記録の詳細画面

    URL例：
    /ouchi-calendar/records/absence/1/

    pk は AbsenceRecord の id
    """

    # ログイン中ユーザーの家族に属する子どもの記録だけ取得する
    record = get_object_or_404(
        AbsenceRecord.objects.select_related("child").prefetch_related("attachments"),
        pk=pk,
        child__family=request.user.family,
    )
    
    # 同じ子ども・同じ日付の排便記録を探す
    bowel_record = BowelMovementRecord.objects.filter(
        child=record.child,
        record_date=record.record_date,
    ).first()

    # 日付を 2026/5/6（水）形式にする
    page_date = _format_japanese_date(record.record_date)
    day_str = record.record_date.isoformat()
    
    context = {
        "record": record,
        "record_type": "absence",
        "page_date": page_date,
        "day_str": day_str,
        "bowel_record": bowel_record,
        "absence_record": record,
    }

    return render(request, "records/record_detail.html", context)

@login_required
def bowel_record_edit_view(request, pk):
    """
    排便記録の編集画面

    ・登録済みの排便記録をフォームに表示する
    ・内容を更新する
    ・新しい添付ファイルを追加する
    ・チェックされた既存添付ファイルを削除する
    """

    # 編集対象の排便記録を取得
    # child__family=request.user.family により、他の家族の記録は編集できないようにする
    record = get_object_or_404(
        BowelMovementRecord.objects.select_related("child").prefetch_related("attachments"),
        pk=pk,
        child__family=request.user.family,
    )
    
    # 同じ子ども・同じ日付の欠席記録を探す
    absence_record = AbsenceRecord.objects.filter(
        child=record.child,
        record_date=record.record_date,
    ).first()

    # 家族の子ども一覧
    children = Child.objects.filter(
        family=request.user.family
    ).order_by("id")

    if request.method == "POST":
        # instance=record を指定すると「新規作成」ではなく「既存データの更新」になる
        bowel_form = BowelMovementRecordForm(
            request.POST,
            instance=record,
        )
        
        # 欠席フォームはこの画面では保存しないので空で用意する
        absence_form = AbsenceRecordForm()

        # POSTされた日付を取得する
        posted_date = _parse_date(request.POST.get("record_date"))
        if posted_date is None:
            posted_date = record.record_date

        # POSTされた子どもを取得する
        child_id = request.POST.get("child_id")
        child = get_object_or_404(
            Child,
            id=child_id,
            family=request.user.family,
        )

        if bowel_form.is_valid():
            updated_record = bowel_form.save(commit=False)

            # child と record_date はフォームに含めていないので、viewでセットする
            updated_record.child = child
            updated_record.record_date = posted_date
            updated_record.save()
            
            # 既存添付ファイルの削除
            # チェックされた添付ファイルIDを取得する
            delete_attachment_ids = request.POST.getlist("delete_attachments")

            # この記録に紐づく添付だけ削除対象にする
            attachments_to_delete = updated_record.attachments.filter(
                id__in=delete_attachment_ids,
            )

            for attachment in attachments_to_delete:
                # media内の実ファイルを削除する
                if attachment.file:
                    attachment.file.delete(save=False)

                # DB上の添付レコードを削除する
                attachment.delete()
            
            # 新しい添付ファイルの追加
            # name="bowel_files" の input から複数ファイルを取得する
            for uploaded_file in request.FILES.getlist("bowel_files"):
                BowelMovementAttachment.objects.create(
                    bowel_movement_record=updated_record,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                )

            # 更新した記録の日付をURL用の文字列にする
            day_str = updated_record.record_date.isoformat()

            # 予定・記録概要画面へ戻る
            return redirect("schedule:day", date=day_str)
        
    else:
        # GET時：既存データをフォームに入れて表示する
        bowel_form = BowelMovementRecordForm(instance=record)
        absence_form = AbsenceRecordForm()

    context = {
        "mode": "edit",
        "record_type": "bowel",
        "bowel_form": bowel_form,
        "absence_form": absence_form,
        "date": record.record_date.isoformat(),
        "children": children,
        "selected_child_id": record.child.id,
        "record": record,
        "attachments": record.attachments.all(),
        "bowel_record": record,
        "absence_record": absence_record,
    }

    return render(request, "records/record_form.html", context)

@login_required
def absence_record_edit_view(request, pk):
    """
    欠席記録の編集画面

    ・登録済みの欠席記録をフォームに表示する
    ・内容を更新する
    ・新しい添付ファイルを追加する
    ・チェックされた既存添付ファイルを削除する
    """

    record = get_object_or_404(
        AbsenceRecord.objects.select_related("child").prefetch_related("attachments"),
        pk=pk,
        child__family=request.user.family,
    )
    
    # 同じ子ども・同じ日付の排便記録を探す
    bowel_record = BowelMovementRecord.objects.filter(
        child=record.child,
        record_date=record.record_date,
    ).first()

    children = Child.objects.filter(
        family=request.user.family
    ).order_by("id")

    if request.method == "POST":
        # 排便フォームはこの画面では保存しない
        bowel_form = BowelMovementRecordForm()

        # instance=record を指定することで、欠席記録を更新する
        absence_form = AbsenceRecordForm(
            request.POST,
            instance=record,
        )

        posted_date = _parse_date(request.POST.get("record_date"))
        if posted_date is None:
            posted_date = record.record_date

        child_id = request.POST.get("child_id")
        child = get_object_or_404(
            Child,
            id=child_id,
            family=request.user.family,
        )
        
        if absence_form.is_valid():
            updated_record = absence_form.save(commit=False)
            updated_record.child = child
            updated_record.record_date = posted_date
            updated_record.save()
            
            # 既存添付ファイルの削除
            delete_attachment_ids = request.POST.getlist("delete_attachments")

            attachments_to_delete = updated_record.attachments.filter(
                id__in=delete_attachment_ids,
            )

            for attachment in attachments_to_delete:
                if attachment.file:
                    attachment.file.delete(save=False)
                attachment.delete()

            # 新しい添付ファイルの追加
            for uploaded_file in request.FILES.getlist("absence_files"):
                AbsenceAttachment.objects.create(
                    absence_record=updated_record,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                )

            # 更新した記録の日付をURL用の文字列にする
            day_str = updated_record.record_date.isoformat()

            # 予定・記録概要画面へ戻る
            return redirect("schedule:day", date=day_str)
        
    else:
        bowel_form = BowelMovementRecordForm()
        absence_form = AbsenceRecordForm(instance=record)

    context = {
        "mode": "edit",
        "record_type": "absence",
        "bowel_form": bowel_form,
        "absence_form": absence_form,
        "date": record.record_date.isoformat(),
        "children": children,
        "selected_child_id": record.child.id,
        "record": record,
        "attachments": record.attachments.all(),
        "bowel_record": bowel_record,
        "absence_record": record,
    }

    return render(request, "records/record_form.html", context)

@login_required
def bowel_record_delete_view(request, pk):

    record = get_object_or_404(
        BowelMovementRecord,
        pk=pk,
        child__family=request.user.family,
    )

    day_str = record.record_date.isoformat()

    # OK押下時
    if request.method == "POST":

        # 添付ファイル本体削除
        for attachment in record.attachments.all():
            if attachment.file:
                attachment.file.delete(save=False)

        # DBレコード削除
        record.delete()

        return redirect("schedule:day", date=day_str)

    return redirect("records:bowel_edit", pk=record.pk)
    
@login_required
def absence_record_delete_view(request, pk):

    record = get_object_or_404(
        AbsenceRecord,
        pk=pk,
        child__family=request.user.family,
    )

    day_str = record.record_date.isoformat()

    if request.method == "POST":

        for attachment in record.attachments.all():
            if attachment.file:
                attachment.file.delete(save=False)

        record.delete()

        return redirect("schedule:day", date=day_str)

    return redirect("records:absence_edit", pk=record.pk)
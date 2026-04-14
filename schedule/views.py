from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from .models import Schedule
from attachments.models import ScheduleAttachment
from comments.forms import ScheduleCommentForm
from comments.models import ScheduleComment
from .forms import ScheduleForm

import calendar

@login_required
def month_view(request):
    # ---表示する「年」と「月」を決める---
    # 今日の日付を取得
    today = timezone.localdate()
    # まずは今月を表示
    year = today.year
    month = today.month

    # ---その月のカレンダーの形を作る---
    # 月曜始まりのカレンダーを作る
    cal = calendar.Calendar(firstweekday=0)
    # monthdatescalendar(year, month)：その月を「1週間ごとのまとまり」で返してくれる便利関数
    # その月を「週ごとの日付リスト」にする。（その月以外の日付も、1週間をそろえるために入る）
    # 例：[[3/30, 3/31, 4/1, 4/2, 4/3, 4/4, 4/5], [4/6,  4/7,  4/8, 4/9, 4/10,4/11,4/12], ・・・]
    month_weeks = cal.monthdatescalendar(year, month)

    # ---その月の開始日・終了日を作る---
    # その月の開始日。月の1日を作る
    month_start = date(year, month, 1)
    # 次の月の開始日。次の月の1日を作る。12月だけは翌年1月に進める
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)

    # ---その月の予定を取得する---
    # start_at が「その月の1日以上」かつ「次の月の1日未満」の予定を取る
    schedules = Schedule.objects.filter(
        family=request.user.family,
        start_at__date__gte=month_start,
        start_at__date__lt=next_month_start,
    ).order_by("start_at")

    # ---日付ごとに予定をまとめる---
    # 日付ごとに予定をまとめる辞書（「この日にはこの予定たちがある」と取り出しやすくするための辞書）を作る
    # 例：template で使いやすいように、{"2026-03-09": [schedule1, schedule2],"2026-03-10": [schedule3],}の形にする
    schedules_by_date = {}

    for schedule in schedules:
        # date().isoformat() で "YYYY-MM-DD" 形式の文字列にする
        day_key = schedule.start_at.date().isoformat()

        # まだその日付の入れ物がなければ、空リストを作る
        if day_key not in schedules_by_date:
            schedules_by_date[day_key] = []

        # その日付のリストに予定を追加
        schedules_by_date[day_key].append(schedule)

    #---templateで使いやすい「カレンダー表示用データ」を作る---
    # 1日ごとに、
    # {
    #   "date": 日付,
    #   "date_str": "2026-03-09",
    #   "is_current_month": True / False,
    #   "schedules": [その日の予定一覧],
    # }
    # の形にしておく
    
    # template では、
    # 日付は cell.date.day
    # URL用の日付文字列は cell.date_str
    # 今月かどうかは cell.is_current_month
    # 今日かどうかは cell.is_today
    # 予定一覧は cell.schedules
    # として使える
    calendar_rows = []

    for week in month_weeks:
        week_data = []

        for day in week:
            day_str = day.isoformat()

            week_data.append({
                "date": day,
                "date_str": day_str,
                "is_current_month": (day.month == month),
                "is_today": (day == today),
                "schedules": schedules_by_date.get(day_str, []),
            })

        calendar_rows.append(week_data)

    context = {
        "year": year,
        "month": month,
        "week_names": ["月", "火", "水", "木", "金", "土", "日"],
        "calendar_rows": calendar_rows,
        "family": request.user.family,
    }

    return render(request, "schedule/month.html", context)



# ①URLから受け取った "2026-02-23" のような文字列を、Pythonで扱える date型 に変換する関数
def _parse_date(date_str: str):
    """
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

# ②その日1日分の範囲を作る関数
# 例: 2026-02-23 なら 2026-02-23 00:00 〜 2026-02-24 00:00 の範囲を作る。
# その間にある予定を取得するため    
def _day_range(target_date):
    """
    datetime.combine(target_date, time.min)
    → date(2026,2,23)+00:00をつくる
    
    timedelta(days=1)
    → 1日足す。2026-02-23 00:00 + 1日 = 2026-02-24 00:00
    
    timezone.make_aware(...)
    → タイムゾーン付き日時に変換する
    
    PythonとDjangoでは、日時には2種類ある
    タイムゾーンなし（naive）→「2026-02-23 10:00」とだけ書いてある状態。日本時間の10時？アメリカ時間の10時？
    タイムゾーンあり（aware）→「日本時間2026-02-23 10:00」と明確
    """
    start_naive = datetime.combine(target_date, time.min)
    end_naive = start_naive + timedelta(days=1)
    
    start =timezone.make_aware(start_naive)
    end = timezone.make_aware(end_naive)
    return start, end
    
@login_required
def day_view(request, date):
    # URLの date を date型 に変換
    target_date = _parse_date(date)
    # 不正な日付なら月カレンダーへ戻す
    if target_date is None:
        return redirect("schedule:month")
     # その日の開始・終了時刻を作る
    start_dt,end_dt = _day_range(target_date)
    
    """
    その日の予定だけを取得する
    
    その日の予定だけを取ってくるための条件
    「フィールド名__条件」と書く
    フィールド名__gte → gte = greater than or equal。以上。start_at >= start_dt。
    フィールド名__lt → lt = less than。未満。start_at < end_dt
    start_at が 2026-02-23 00:00 以上 かつ 2026-02-24 00:00 未満
    """
    schedules =Schedule.objects.filter(
        family = request.user.family,
        start_at__gte=start_dt,
        start_at__lt=end_dt,
    ).select_related(
        "user"
    ).prefetch_related(
        "user_memberships__user",
        "child_memberships__child",
    ).order_by("start_at")
    
    # 画面表示用の日付文字列を作る
    week_map = ["月", "火", "水", "木", "金", "土", "日"]
    # weekday()は曜日を数字で返す関数で、weekday() が返した数字をそのままインデックスとして使っている
    weekday = week_map[target_date.weekday()]
    page_date = f"{target_date.year}/{target_date.month}/{target_date.day}({weekday})"

    context = {
        "date": date, # URL用
        "page_date": page_date, # 画面表示用
        "schedules": schedules,
    }

    return render(request, "schedule/day.html", context)


@login_required
def create_choice_view(request, date):
    context = {
        "date": date,
    }
    
    return render(request, "schedule/create_choice.html", context)


@login_required
def schedule_create_view(request):
    # create-choice 画面から ?date=2026-04-10 のように受け取る想定
    date_str = request.GET.get("date") 
    
    if request.method == "POST":
        form = ScheduleForm(
            request.POST,
            request.FILES, 
            target_date=date_str,
            family=request.user.family,
        )
        
        # 予定新規作成時は、まだ schedule が保存前なので
        # user=request.user を渡して宛先候補を出す
        comment_form = ScheduleCommentForm(
            request.POST,
            user=request.user,
        )
            
        if form.is_valid() and comment_form.is_valid():
            # form.instance：そのフォームが今保存対象として持っているモデルインスタンス
            # このフォームで保存する予定の family を、ログイン中ユーザーの family にする
            form.instance.family = request.user.family
            schedule = form.save()
            
            # 複数ファイルをまとめて取得
            uploaded_files = request.FILES.getlist('attachments')

            for uploaded_file in uploaded_files:
                ScheduleAttachment.objects.create(
                    schedule=schedule,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                )
                
            # コメント本文が入っているときだけ保存する
            body = comment_form.cleaned_data.get("body")
            to_user = comment_form.cleaned_data.get("to_user")

            # body が空文字でなければコメント作成
            if body:
                ScheduleComment.objects.create(
                    schedule=schedule,                              # どの予定へのコメントか
                    from_user=request.user,                         # 投稿者はログイン中ユーザー
                    to_user=to_user,                                # 宛先
                    comment_type=ScheduleComment.COMMENT_TYPE_USER, # 通常のユーザーコメント
                    body=body,                                      # コメント本文
                )

            day_str = schedule.start_at.date().isoformat() # 予定・記録概要画面のURLに渡すには 文字列 が必要だから、.isoformat()
            return redirect("schedule:day", date=day_str)
    
    else:
        form = ScheduleForm(
            target_date=date_str,
            family=request.user.family, 
        )
        
        comment_form = ScheduleCommentForm(
            user=request.user,
        )
        
    context = {
        "mode": "create", # 作成/編集表示
        "date": date_str,  # 戻るリンク用
        "form": form, # 入力フォーム
        "comment_form": comment_form,
    }
    
    return render(request, "schedule/schedule_form.html", context)
    
@login_required
def schedule_detail_view(request, pk):
    # ログイン中ユーザーの家族に属する予定だけ取得する
    schedule = get_object_or_404(
        Schedule.objects.prefetch_related("attachments"),
        pk=pk,
        family=request.user.family
    )
    
    # 戻るリンク用に、予定の日付を "YYYY-MM-DD" 文字列にする
    day_str = schedule.start_at.date().isoformat()
    
    # 画面表示用の日付文字列を作る
    week_map = ["月", "火", "水", "木", "金", "土", "日"]
    start_date = schedule.start_at.date()
    start_weekday = week_map[start_date.weekday()]
    page_date = f"{start_date.year}/{start_date.month}/{start_date.day}（{start_weekday}）"
    
    # 連続対応の終了日がある場合の画面表示用の日付文字列を作る
    coordination_end_date_display = None
    
    if schedule.coordination_end_date:
        end_date = schedule.coordination_end_date
        end_weekday = week_map[end_date.weekday()]
        coordination_end_date_display = (
            f"{end_date.year}/{end_date.month}/{end_date.day}（{end_weekday}）"
        )

    # ステータスごとの補助メッセージを作る
    # 対応・調整が必要な予定のときに表示する
    status_message = ""

    if schedule.requires_coordination:
        if schedule.status == Schedule.Status.CONFIRMED:
            status_message = "＊ この予定の調整は完了しています。"
        elif schedule.status == Schedule.Status.ADJUSTING:
            status_message = "＊ 担当者の返事が分かったら、編集からステータスを「確定」または「不可」に変更してください。"
        elif schedule.status == Schedule.Status.IMPOSSIBLE:
            status_message = "＊ 現在、対応できる担当者がいない状態です。"

     # 予定メンバー（大人）を取得
    user_memberships = schedule.user_memberships.select_related("user").all()

    # 予定メンバー（子ども）を取得
    child_memberships = schedule.child_memberships.select_related("child").all()
    
    # 添付ファイルを取得
    attachments = schedule.attachments.all()
    
    # コメントを取得
    # テンプレートで表示しやすいように、from_user と to_user も一緒に取っておく
    comments = schedule.comments.select_related("from_user", "to_user").all()
    
    context = {
        "schedule": schedule,
        "day_str": day_str,  # day画面へ戻るために使う
        "page_date": page_date,  # 画面表示用の日付
        "coordination_end_date_display": coordination_end_date_display,  # 画面表示用の終了日
        "status_message": status_message,  # ステータスの補助文
        "user_memberships": user_memberships,
        "child_memberships": child_memberships,
        "attachments": attachments,
        "comments": comments, 
    }
    
    return render(request, "schedule/schedule_detail.html", context)
    
    
@login_required
def schedule_edit_view(request, pk):
    # 1. 編集対象の予定を取得する
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family = request.user.family
    )
    
    # 2. 戻るリンク用の日付文字列を作る
    date_str = schedule.start_at.date().isoformat()
    
    # 3. POSTかGETかで処理を分ける
    # GET  : 画面を開いたとき → 既存内容入りフォームを表示
    # POST : 保存ボタンを押したとき → 入力内容で更新する
    if request.method == "POST":
        # POSTのときは、送信されたデータ(request.POST)をフォームに入れる
        # instance=schedule を付けることで、
        # 「新規作成」ではなく「この予定を更新する」動きになる。「この schedule の内容を使ってフォームを作ってください」という意味
        form = ScheduleForm(
            request.POST,
            request.FILES,
            instance=schedule,
            family=request.user.family,
        )
    
        # 入力チェックOKなら保存する
        if form.is_valid():
            # family は元の予定に入っているが、
            # 念のためログイン中ユーザーの家族をセットしておく
            form.instance.family = request.user.family
            updated_schedule = form.save()
            
            # ① 削除チェックされた既存添付を削除
            # テンプレートの checkbox にチェックされた添付ID一覧を取得
            delete_attachment_ids = request.POST.getlist("delete_attachments")

            attachments_to_delete = ScheduleAttachment.objects.filter(
                id__in=delete_attachment_ids,
                schedule=updated_schedule,  # 削除はこの予定の添付だけに限定する
            )

            for attachment in attachments_to_delete:
                # 先に media 内のファイル本体を削除
                if attachment.file:
                    attachment.file.delete(save=False)

                # 次にDBレコードを削除
                attachment.delete()

            # ② 新しく選んだ添付ファイルを追加保存
            uploaded_files = request.FILES.getlist("attachments")

            for uploaded_file in uploaded_files:
                ScheduleAttachment.objects.create(
                    schedule=updated_schedule,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                )

            # 保存後は、その予定が属する day画面 に戻る
            day_str = updated_schedule.start_at.date().isoformat()
            return redirect("schedule:day", date=day_str)

    else:
        # GETのときは、既存の予定内容を初期表示したフォームを作る
        # instance=schedule があることで、
        # title や memo などが最初から入った状態になる
        form = ScheduleForm(
            instance=schedule,
            family=request.user.family,
        )    
    
    # 4. template に渡す    
    context = {
        "mode": "edit",
        "date": date_str,
        "form": form,
        "schedule": schedule,
        "attachments": schedule.attachments.all(),
    }
    
    return render(request, "schedule/schedule_form.html", context)
    
    
@login_required
def schedule_delete_view(request, pk):
    # 1. 削除対象の予定を取得する
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family = request.user.family
    )
    
    # 2. 戻るリンク用の日付文字列を作る
    day_str = schedule.start_at.date().isoformat()
    
    # 3. POSTなら本当に削除する
    # 削除後は、その日の day画面 に戻る
    if request.method == "POST":
        schedule.delete()
        return redirect("schedule:day", date=day_str)

    context = {
        "schedule": schedule,
        "day_str": day_str,
    }
    
    return render(request, "schedule/schedule_confirm_delete.html", context)
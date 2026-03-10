from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from .models import Schedule
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
    ).order_by("start_at")
    
    context = {
        "date": date,
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
    date_str = request.GET.get("date")  # create-choice から ?date= で渡す想定
    
    if request.method == "POST":
        form = ScheduleForm(request.POST, target_date=date_str)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.family = request.user.family
            schedule.save()

            day_str = schedule.start_at.date().isoformat() # 予定・記録概要画面のURLに渡すには 文字列 が必要だから、.isoformat()
            return redirect("schedule:day", date=day_str)
    else:
        form = ScheduleForm(target_date=date_str)
        
    context = {
        "mode": "create", # 作成/編集表示
        "date": date_str,  # 戻るリンク用
        "form": form, # 入力フォーム
    }
    
    return render(request, "schedule/schedule_form.html", context)
    
    
@login_required
def schedule_detail_view(request, pk):
    # ログイン中ユーザーの家族に属する予定だけ取得する
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family=request.user.family
    )
    
    # 戻るリンク用に、予定の日付を "YYYY-MM-DD" 文字列にする
    day_str = schedule.start_at.date().isoformat()
    
    context = {
        "schedule": schedule,
        "day_str": day_str,  # day画面へ戻るために使う
    }
    
    return render(request, "schedule/schedule_detail.html", context)
    
    
@login_required
def schedule_edit_view(request, pk):
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family = request.user.family
    )
    
    context = {
        "mode": "edit",
        "schedule": schedule,
    }
    
    return render(request, "schedule/schedule_form.html", context)
    
    
@login_required
def schedule_delete_view(request, pk):
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family = request.user.family
    )
    
    context = {
        "schedule": schedule,
    }
    
    return render(request, "schedule/schedule_confirm_delete.html", context)
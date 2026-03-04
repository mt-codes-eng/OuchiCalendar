from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, time, timedelta
from django.utils import timezone
from .models import Schedule
from .forms import ScheduleForm

@login_required
def month_view(request):
    context = {}
    return render(request, "schedule/month.html", context)

# ①URLからくるdateは文字列であるため、文字列を日付(date型)に変換する（DBと比較するため）
def _parse_date(date_str: str):
    """
    date_str: str→型ヒント。date_str は str型と書いているだけ。str型を強制するものではない
    datetime.strptime→文字列 から 日付（datetime型）に変換する関数。例"2026-02-23"をdatetime(2026, 2, 23, 0, 0)
    .date()→date型にする。例datetime(2026, 2, 23, 0, 0)をdate(2026, 2, 23)
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except(ValueError,TypeError):
        return None

# ②その日の範囲を作る（2026-02-23 の 00:00〜2026-02-24 の 00:00 までの間にある予定を取得するため）    
def _day_range(target_date):
    """
    datetime.combine(target_date, time.min)→date(2026,2,23)+00:00をつくる
    timedelta(days=1)→1日足す。2026-02-23 00:00 + 1日 = 2026-02-24 00:00
    
    PythonとDjangoでは、日時には2種類ある。
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
    target_date = _parse_date(date)
    if target_date is None:
        return redirect("schedule:month")
    start_dt,end_dt = _day_range(target_date)
    
    """
    その日の予定だけを取ってくるための条件
    「フィールド名__条件」と書く
    フィールド名__gte → gte = greater than or equal。以上。start_at >= start_dt。
    フィールド名__lt → lt = less than。未満。start_at < end_dt
    2026-02-23 00:00 以上 かつ 2026-02-24 00:00 未満
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
    schedule = get_object_or_404(
        Schedule,
        pk=pk,
        family=request.user.family
    )
    
    context = {
        "schedule": schedule,
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
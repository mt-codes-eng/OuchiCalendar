from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from schedule.models import Schedule
from .models import ScheduleComment

@login_required
def comment_recent_view(request):
    """
    コメント新着画面
    """
    # 表示用のリスト（ここに全部まとめる）
    rows = []
    
    # 曜日表示用
    week_map = ["月", "火", "水", "木", "金", "土", "日"]
    
    # ① コメントがあるもの
    comments = (
        ScheduleComment.objects
        .select_related("schedule", "from_user", "to_user", "schedule__user")
        .filter(
            # Q(...) | Q(...) | Q(...)：または条件
            Q(from_user=request.user) | # 自分が投稿したコメント
            Q(to_user=request.user) | # 自分宛てのコメント
            Q(schedule__user=request.user) # 自分が担当者の予定についたコメント
        )
    )

    for comment in comments:
        schedule = comment.schedule
        
        # 予定日付(例：4/14(火))
        schedule_date = schedule.start_at
        weekday = week_map[schedule_date.weekday()]
        schedule_date_display = (
            f"{schedule_date.month}/{schedule_date.day}({weekday})"
        )

        # コメント投稿日時(例：5/15（日）16:00)
        created_at = comment.created_at
        weekday = week_map[created_at.weekday()]
        created_at_display = (
            f"{created_at.month}/{created_at.day}({weekday})"
            f"{created_at.hour}:{created_at.minute:02}"
        )
        
        # 表示用データを1件分まとめる
        rows.append({
            "schedule": schedule, # クリック遷移用
            "schedule_date_display": schedule_date_display,
            "coordination_display": schedule.display_coordination,
            "assigned_user": schedule.user,
            "comment_user": comment.from_user,
            "created_at_display": created_at_display,
            "created_at": created_at, # 並び替え用
            "body": comment.body,
        })
        
    # ② コメントがまだない「対応・調整あり」の予定
    schedules = (
        Schedule.objects
        .select_related("user")
        .filter(
            family=request.user.family,
            requires_coordination=True,   # 対応・調整あり
            user=request.user,            # 自分が担当者
            comments__isnull=True,        # コメントが1件もない
        )
    )

    for schedule in schedules:
        # 予定日付(例：4/14(火))
        schedule_date = schedule.start_at
        weekday = week_map[schedule_date.weekday()]
        schedule_date_display = (
            f"{schedule_date.month}/{schedule_date.day}({weekday})"
        )

        # コメント投稿日時の代わりに「予定作成日時」(例：5/15（日）16:00)
        created_at = schedule.created_at
        weekday = week_map[created_at.weekday()]
        created_at_display = (
            f"{created_at.month}/{created_at.day}({weekday})"
            f"{created_at.hour}:{created_at.minute:02}"
        )

        # 表示用データを1件分まとめる-
        rows.append({
            "schedule": schedule,
            "schedule_date_display": schedule_date_display,
            "coordination_display": schedule.display_coordination,
            "assigned_user": schedule.user,
            "comment_user": None,   # コメント者なし
            "created_at_display": created_at_display,
            "created_at": created_at,
            "body": "【対応依頼】担当者に選ばれました。",
        })
        
    # ③ 新しい順に並び替え
    rows = sorted(
        rows,
        key=lambda row: row["created_at"],
        reverse=True
    )[:20]
        
    # ④ テンプレートへ
    context = {
        "rows": rows,
    }

    return render(request, "comments/comment_recent.html", context)
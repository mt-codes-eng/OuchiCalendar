from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ScheduleComment

@login_required
def comment_recent_view(request):
    """
    コメント新着画面
    """
    # コメント取得
    comments = (
        ScheduleComment.objects
        .select_related("schedule", "from_user", "to_user", "schedule__user")
        .filter(
            # Q(...) | Q(...) | Q(...)：または条件
            Q(from_user=request.user) | # 自分が投稿したコメント
            Q(to_user=request.user) | # 自分宛てのコメント
            Q(schedule__user=request.user) # 自分が担当者の予定についたコメント
        )
        .order_by("-created_at")
        .distinct()[:20] # distinct()：重複防止。 # 最初は20件表示とする
    )

    # 表示用データを作る
    week_map = ["月", "火", "水", "木", "金", "土", "日"]

    for comment in comments:

        # 予定日付
        schedule_date = comment.schedule.start_at
        weekday = week_map[schedule_date.weekday()]
        # 例：4/14（火）
        comment.schedule_date_display = (
            f"{schedule_date.month}/{schedule_date.day}（{weekday}）"
        )

        # コメント投稿日時
        created_at = comment.created_at
        weekday = week_map[created_at.weekday()]
        # 例：5/15（日）16:00
        comment.created_at_display = (
            f"{created_at.month}/{created_at.day}（{weekday}）"
            f"{created_at.hour}:{created_at.minute:02}"
        )

    context = {
        "comments": comments,
    }

    return render(request, "comments/comment_recent.html", context)
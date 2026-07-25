from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from schedule.models import Schedule
from .models import ScheduleComment

def _make_comment_preview(body, max_length=20):
    """
    コメント新着画面に表示する短いコメント本文を作る

    ・改行や連続する空白を1つの空白にまとめる
    ・20文字以内ならそのまま表示する
    ・20文字を超える場合は、先頭20文字＋「…」にする
    """
    # bodyがNoneの場合にもエラーにならないように空文字へ変換する
    text = body or ""

    # 改行や連続する空白を、1つの半角スペースにまとめる
    text = " ".join(text.split())

    # 20文字以内なら、そのまま返す
    if len(text) <= max_length:
        return text

    # 20文字を超える場合は、先頭20文字に「…」を付ける
    return text[:max_length] + "…"

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
            "body": comment.body, # コメント全文
            "body_preview": _make_comment_preview(comment.body), # コメント新着画面に表示する先頭20文字
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
        
        system_body = "【対応依頼】担当者に選ばれました。"

        # 表示用データを1件分まとめる
        rows.append({
            "schedule": schedule,
            "schedule_date_display": schedule_date_display,
            "coordination_display": schedule.display_coordination,
            "assigned_user": schedule.user,
            "comment_user": None,   # コメント者なし
            "created_at_display": created_at_display,
            "created_at": created_at,
            "body": system_body,
            "body_preview": _make_comment_preview(system_body),
        })
        
    # ③ 予定が早い順 or コメント投稿日順（新着順）で並び替え(デフォルトは新着順)
    # 並び替え種類取得 予定が早い順URL：/comments/recent/?sort=schedule or コメント投稿日順（新着順）URL：/comments/recent/?sort=comment
    sort = request.GET.get("sort", "comment")
    
    # 並び替え
    if sort == "schedule":
        # 予定日が早い順
        # sorted()：sorted(リスト, key=基準, reverse=並び順)
        rows = sorted(
        rows, # 並び替え対象（リスト）
        key=lambda row: row["schedule"].start_at # 予定開始日時で比較
        )
    else:
        # コメント投稿日順（新着順）（デフォルト）
        rows = sorted(
            rows,
            key=lambda row: row["created_at"],
            reverse=True
        )
        
    # ④ テンプレートへ
    context = {
        "rows": rows,
        "sort": sort,
        "today_str": timezone.localdate().strftime("%Y-%m-%d"),
    }

    return render(request, "comments/comment_recent.html", context)
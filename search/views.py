from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from collections import defaultdict

from schedule.models import Schedule
from records.models import BowelMovementRecord, AbsenceRecord
from color_assignments.models import FamilyColorAssignment

def _format_japanese_date(target_date):
    """
    date型を画面表示用の文字列にする
    例：date(2026, 5, 6) → "2026/5/6（水）"
    """
    week_map = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = week_map[target_date.weekday()]
    return f"{target_date.year}/{target_date.month}/{target_date.day}（{weekday}）"

def _get_color_map(family):
    """
    家族ごとの色設定を、画面で使いやすい形にまとめる関数

    戻り値のイメージ：
    {
        "shared": "#c2bbb2",
        "users": {
            1: "#ff7f7f",
            2: "#7fbfff",
        },
        "children": {
            3: "#7fff7f",
        },
    }
    """

    # 色が未設定だったときの初期値
    color_map = {
        "shared": "#cccccc",   # 合同予定カラー
        "users": {},           # 大人メンバー用カラー
        "children": {},        # 子ども用カラー
    }

    # この家族に設定されている色を全部取得
    assignments = FamilyColorAssignment.objects.filter(
        family=family
    )

    for assignment in assignments:
        # color_code から "#ff7f7f" のような色コードに変換
        hex_color = assignment.get_hex_color()

        # 合同予定カラー
        if assignment.assign_type == FamilyColorAssignment.AssignType.SHARED:
            color_map["shared"] = hex_color

        # 大人メンバーの個人カラー
        elif assignment.assign_type == FamilyColorAssignment.AssignType.USER:
            color_map["users"][assignment.user_id] = hex_color

        # 子どもの個人カラー
        elif assignment.assign_type == FamilyColorAssignment.AssignType.CHILD:
            color_map["children"][assignment.child_id] = hex_color

    return color_map

@login_required
def search_view(request):
    """
    検索画面

    検索対象：
    ・予定タイトル
    ・予定メモ
    ・予定添付ファイル名
    ・予定コメント本文
    ・排便記録メモ
    ・排便記録の気になることメモ
    ・排便添付ファイル名
    ・欠席記録メモ
    ・欠席添付ファイル名
    """

    # 検索フォームから入力された q を受け取る
    # request.GET → URLの ?q=会議 のような値が入っている
    # strip() は前後の空白を消す
    keyword = request.GET.get("q", "").strip()
    
    # 家族の色設定をまとめて取得する
    # 予定・記録に display_color を付けるために使う
    color_map = _get_color_map(request.user.family)

    # 日付ごとに検索結果を入れる箱
    # 普通の辞書: grouped_results["2026-05-15"] = []
    # defaultdict(list) → 「最初から空リストを持っている辞書」。存在しないキーでも自動で [] を作ってくれる
    grouped_results = defaultdict(list)

    # キーワードが入力されているときだけ検索する
    if keyword:
        # -----------------------------
        # 予定を検索
        # -----------------------------
        schedules = Schedule.objects.filter(
            family=request.user.family,
        ).filter(
            # icontains → i = 大文字小文字を区別しない。contains = 含む
            Q(title__icontains=keyword) | # title に keyword が含まれる
            Q(memo__icontains=keyword) | # 予定メモに含まれる
            Q(attachments__file_name__icontains=keyword) | # 添付ファイル名に含まれる
            Q(comments__body__icontains=keyword) # コメント本文に含まれる
        ).select_related(
            "user", # user(ForeignKey)を一緒に取得
        ).prefetch_related(
            "user_memberships__user", # 多対多や逆参照をまとめて取得
            "child_memberships__child",
            "attachments",
            "comments",
        ).annotate(
            # コメント数を数える
            comment_count=Count("comments", distinct=True),
            # 添付ファイルが1個以上あるか判定するために数える
            attachment_count=Count("attachments", distinct=True),
        ).distinct() # 重複削除。添付やコメントが複数あると同じ予定が重複して取得されることがあるため必要

        # 取得した予定を日付ごとにまとめる
        for schedule in schedules:
             # 大人メンバー一覧をリストにする
            user_memberships = list(schedule.user_memberships.all())

            # 子どもメンバー一覧をリストにする
            child_memberships = list(schedule.child_memberships.all())

            # 予定メンバーの人数を数える
            member_count = len(user_memberships) + len(child_memberships)

            # 対応・調整が必要な予定の場合
            if schedule.requires_coordination:
                # 担当者がいる場合は担当者カラーを使う
                if schedule.user_id:
                    schedule.display_color = color_map["users"].get(
                        schedule.user_id,
                        "#cccccc"
                    )
                # 担当者が未定ならグレー
                else:
                    schedule.display_color = "#cccccc"

            # 対応・調整が不要な通常予定の場合
            else:
                # 予定メンバーが1人だけの場合
                if member_count == 1:
                    # 大人メンバー1人の予定
                    if user_memberships:
                        user_id = user_memberships[0].user_id
                        schedule.display_color = color_map["users"].get(
                            user_id,
                            "#cccccc"
                        )

                    # 子どもメンバー1人の予定
                    else:
                        child_id = child_memberships[0].child_id
                        schedule.display_color = color_map["children"].get(
                            child_id,
                            "#cccccc"
                        )

                # 予定メンバーが複数人、または0人の場合は合同予定カラー
                else:
                    schedule.display_color = color_map["shared"]
                    
            result_date = timezone.localdate(schedule.start_at)

            grouped_results[result_date].append({
                "type": "schedule", # 種類
                "object": schedule, # 実際のScheduleオブジェクト
            })

        # -----------------------------
        # 排便記録を検索
        # -----------------------------
        bowel_records = BowelMovementRecord.objects.filter(
            child__family=request.user.family,
        ).filter(
            Q(memo__icontains=keyword) | # メモ検索
            Q(concern_memo__icontains=keyword) | # 気になることメモ検索
            Q(attachments__file_name__icontains=keyword) # 添付ファイル名検索
        ).select_related(
            "child", # child(ForeignKey)をまとめて取得
        ).prefetch_related(
            "attachments", # 添付をまとめて取得
        ).annotate(
            # 排便記録に添付ファイルがあるか判定するために数える
            attachment_count=Count("attachments", distinct=True),
        ).distinct()

        # 排便記録を日付ごとに追加
        for record in bowel_records:
            # 記録は子どものカラーを使う
            record.display_color = color_map["children"].get(
                record.child_id,
                "#cccccc"
            )
            grouped_results[record.record_date].append({
                "type": "bowel",
                "object": record,
            })

        # -----------------------------
        # 欠席記録を検索
        # -----------------------------
        absence_records = AbsenceRecord.objects.filter(
            child__family=request.user.family,
        ).filter(
            Q(memo__icontains=keyword) | # メモ検索
            Q(attachments__file_name__icontains=keyword) # 添付ファイル名検索
        ).select_related(
            "child",
        ).prefetch_related(
            "attachments",
        ).annotate(
            # 欠席記録に添付ファイルがあるか判定するために数える
            attachment_count=Count("attachments", distinct=True),
        ).distinct()

        # 欠席記録を日付ごとに追加
        for record in absence_records:
            # 記録は子どものカラーを使う
            record.display_color = color_map["children"].get(
                record.child_id,
                "#cccccc"
            )

            grouped_results[record.record_date].append({
                "type": "absence",
                "object": record,
            })
            
    # テンプレートで扱いやすい形に変換する
    results_by_date = []
    
    # grouped_results.keys() → 日付一覧
    # sorted(..., reverse=True) → 新しい日付順に並べる
    for result_date in sorted(grouped_results.keys(), reverse=True):
        results_by_date.append({
            "date": result_date, # 元の日付
            "date_display": _format_japanese_date(result_date), # 日本語表示用 例: 2026/5/15（金）
            "items": grouped_results[result_date], # その日の検索結果一覧
        })
            
    context = {
        "today_str": timezone.localdate().strftime("%Y-%m-%d"),
        "keyword": keyword,
        "results_by_date": results_by_date, # 日付ごとに整理済みの検索結果
    }

    return render(request, "search/search.html", context)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from collections import defaultdict
from datetime import date, datetime, time

from records.models import AbsenceRecord
from schedule.models import Schedule
from children.models import Child
from color_assignments.models import FamilyColorAssignment
from color_assignments.constants import COLOR_HEX_MAP

def _get_next_month(year, month):
    """
    指定年月の翌月1日を返す関数
    例：2026年5月 → 2026年6月1日
    """
    if month == 12:
        return date(year + 1, 1, 1)

    return date(year, month + 1, 1)

def _get_month_range(year, month):
    """
    指定された年月の開始日と終了日を作る関数
    月初日と翌月初日を返す
    
    例：
    2026年5月なら
    start_date = 2026-05-01
    end_date   = 2026-06-01
    record_date__gte=start_date(__gte：以上)
    record_date__lt=end_date(__lt：未満)

    と使うことで、5月分だけ取得できる。
    """
    start_date = date(year, month, 1)
    end_date = _get_next_month(year, month)

    return start_date, end_date

def _make_aware_datetime(target_date):
    """
    date型を timezone 対応の datetime型 に変換する関数
    
    AbsenceRecord.record_date は date型
    Schedule.start_at は datetime型
    なので、月単位で検索するときは date型を datetime型に変換して使う
    """
    # 現在のタイムゾーン（例：Asia/Tokyo）を取得
    current_timezone = timezone.get_current_timezone()

    # date型に「00:00:00」を付けて datetime型にする
    naive_datetime = datetime.combine(
        target_date,
        time.min,
    )

    # timezone情報を付ける
    aware_datetime = timezone.make_aware(
        naive_datetime,
        current_timezone,
    )

    # 完成した timezone対応datetime型 を返す
    return aware_datetime

def _get_child_color(child, family):
    """
    子どもの個人カラーを取得する関数

    FamilyColorAssignment に子どもの色設定があれば、その色を返す
    なければグレーを返す
    """
    # この家族・この子どものカラー設定を探す
    color_assignment = FamilyColorAssignment.objects.filter(
        family=family,
        child=child,
        assign_type=FamilyColorAssignment.AssignType.CHILD,
    ).first()

    # 色設定が存在する場合
    if color_assignment:
        # color_code に対応するHEXカラーを取得。辞書.get(キー, 見つからなかった時の値)
        # 見つからなければグレー
        return COLOR_HEX_MAP.get(color_assignment.color_code, "#cccccc")

    # 色設定自体が無い場合もグレー
    return "#cccccc"

def _get_user_color(user, family):
    """
    大人メンバーの個人カラーを取得する関数
    """
    color_assignment = FamilyColorAssignment.objects.filter(
        family=family,
        user=user,
        assign_type=FamilyColorAssignment.AssignType.USER,
    ).first()

    if color_assignment:
        return COLOR_HEX_MAP.get(color_assignment.color_code, "#cccccc")

    return "#cccccc"

@login_required
def analytics_view(request):
    """
    集計画面

    ① 欠席集計：tab=absence
       子どもごとに、指定月の欠席回数を数える

    ② 対応・調整集計：tab=coordination
       大人ごとに、指定月に対応した予定数を数える
    
    URL例：
    /ouchi-calendar/analytics/?tab=absence&year=2026&month=5
    year と month をURLクエリで受け取る
    """
    # 今日の日付を取得する
    # 例：2026-05-24
    today = timezone.localdate()

    # ① 表示タブを決める
    # URLの ?tab=xxx を取得する。もし tab がURLに無ければ "absence" を使う
    active_tab = request.GET.get("tab", "absence")
    # 想定外の値が来た場合は、欠席集計タブに戻す
    if active_tab not in ["absence", "coordination"]:
        active_tab = "absence"

    # ② 表示年月を決める
    try:
        # URLの ?year=2026 を取得する。もし無ければ今年を使う
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except ValueError:
        # year や month に数字以外が入っていた場合
        # 例：?year=abc
        # エラーにせず、今月に戻す
        year = today.year
        month = today.month

    # 月が 1〜12 以外だった場合も、今月に戻す
    if month < 1 or month > 12:
        year = today.year
        month = today.month
        
    # 指定月の開始日と終了日を作る
    # 例：2026年5月なら
    # start_date = 2026-05-01
    # end_date   = 2026-06-01  
    start_date, end_date = _get_month_range(year, month)

    # ③ 欠席集計
    # ログイン中ユーザーと同じ家族の子ども全員を取得する。グラフや表で毎回同じ順番になるよう id順に並べる
    family_children = Child.objects.filter(
        family=request.user.family,
    ).order_by("id")
    
    # 子どもごとの欠席回数を入れる辞書
    # defaultdict(int) を使うと、初めて使うキーには自動で 0 が入る（まだデータが無い子どもでも、最初は 0回として扱ってくれる）
    # 例：{1: 3, 2: 1,}「子どもID 1 は3回欠席」という意味
    absence_counts = defaultdict(int)

    # 指定月の欠席記録を取得する
    absence_records = AbsenceRecord.objects.filter(
        child__family=request.user.family, # ログイン中ユーザーと同じ家族の子どもだけ（AbsenceRecord の child の family が、ログイン中ユーザーの family と同じ）
        record_date__gte=start_date, # 指定月の初日以上（record_date が start_date 以上）
        record_date__lt=end_date, # 翌月初日未満
        is_absent=True, # 欠席として登録されている記録だけ
    ).select_related("child") # AbsenceRecord と Child をJOINして child も一緒に取得。1回取得し、高速で処理（後から child を使っても追加SQLしない）

    # 実際に欠席記録がある子だけ回数を加算する
    for record in absence_records:
        absence_counts[record.child.id] += 1

    # 最大欠席回数を入れる変数。最初は仮で 0 を入れておく
    # 0回の子どもも含めて family_children を基準にする
    max_absence_count = 0
    
    # 家族の子ども全員の行を作る
    for child in family_children:
        count = absence_counts[child.id]
        # 今までの最大値より大きければ更新する
        if count > max_absence_count:
            max_absence_count = count
    
    # テンプレートに渡すためのリスト
    absence_rows = []
    
    # 家族の子ども全員分の行を作る
    for child in family_children:
        count = absence_counts[child.id]
        # 棒グラフの高さ。最初は0にしておく
        percent = 0
        # 最大値が0より大きい場合だけ計算する（0で割るエラーを防ぐため）
        if max_absence_count > 0:
            percent = int(count / max_absence_count * 100)

        absence_rows.append({
            "name": child.name,
            "count": count,
            "percent": percent, 
            "color": _get_child_color(child, request.user.family),
        })

    # 表示順を名前順にする
    absence_rows = sorted(absence_rows, key=lambda row: row["name"])

    # ④ 対応・調整集計
    # Schedule.start_at は datetime型なので、
    # date型の start_date / end_date を datetime型に変換する
    start_dt = _make_aware_datetime(start_date)
    end_dt = _make_aware_datetime(end_date)
    
    # 大人メンバー全員を取得する
    # 対応回数が0回でも表・グラフに表示するため
    family_users = request.user.__class__.objects.filter(
        family=request.user.family,
    ).order_by("name", "email")
    
    # 大人ごとの対応回数を入れる辞書
    coordination_counts = defaultdict(int)
    # 指定月の「対応済み」と考える予定だけ取得する
    schedules = Schedule.objects.filter(
        family=request.user.family, # ログイン中ユーザーと同じ家族の予定だけ
        start_at__gte=start_dt, # 指定月の初日以降
        start_at__lt=end_dt, # 翌月初日より前
        requires_coordination=True, # 対応・調整が必要な予定だけ
        user__isnull=False, # 担当者が設定されている予定だけ
        status=Schedule.Status.CONFIRMED, # ステータスが「〇 確定」のものだけ
    ).select_related("user")

    for schedule in schedules:
        user = schedule.user
        # 担当者ごとの対応回数を数える
        coordination_counts[user.id] += 1
        
    # 最大対応回数を取得する
    # 0回の人も含めるため、family_users を基準にして最大値を作る
    max_coordination_count = 0
    
    for user in family_users:
        count = coordination_counts[user.id]

        if count > max_coordination_count:
            max_coordination_count = count
    
    # テンプレートに渡すためのリスト
    coordination_rows = []
        
    # 大人ごとの対応回数を、画面表示用データに変換する
    for user in family_users:
        count = coordination_counts[user.id]
        # 棒グラフの高さ
        percent = 0
        # 最大値が0より大きい場合だけ計算する
        if max_coordination_count > 0:
            percent = int(count / max_coordination_count * 100)
        # 画面表示用のデータを追加する
        coordination_rows.append({
            "name": user.name or user.email,
            "count": count,
            "percent": percent,
            "color": _get_user_color(user, request.user.family),
        })
    # 大人メンバーの名前順に並び替える
    coordination_rows = sorted(coordination_rows, key=lambda row: row["name"])
    
    # 縦軸の中央目盛り
    # 最大値が 1 のときは 1,1,0 にならないように、
    # half が 0 のままでもOKにする
    half_absence_count = max_absence_count // 2
    half_coordination_count = max_coordination_count // 2
        
    # ⑤ テンプレートに渡すデータ
    context = {
        "today_str": timezone.localdate().strftime("%Y-%m-%d"),
        "active_tab": active_tab,
        "year": year,
        "month": month,
        "years": range(today.year - 2, today.year + 3),# 年の選択肢。例：今年が2026年なら 2024〜2028
        "months": range(1, 13), # 月の選択肢（1〜12月）
        "absence_rows": absence_rows,
        "coordination_rows": coordination_rows,
        # グラフの縦軸目盛り用
        "max_absence_count": max_absence_count,
        "half_absence_count": half_absence_count,
        "max_coordination_count": max_coordination_count,
        "half_coordination_count": half_coordination_count,
    }

    return render(request, "analytics/index.html", context)
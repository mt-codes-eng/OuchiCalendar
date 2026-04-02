from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from .forms import FamilyProfileForm
from children.models import Child
from django.contrib.auth import get_user_model
from color_assignments.models import FamilyColorAssignment
from color_assignments.constants import COLOR_HEX_MAP
from .utils import is_initial_setup_completed

User = get_user_model()

@login_required
def family_settings_view(request):
    # ログインしているユーザー(request.user)の家族を取り出してfamily という変数に入れる
    family = request.user.family
    # ログイン中のユーザーの家族に属する大人だけを取得する
    adult_members = User.objects.filter(family=family).order_by("id")
    # children_childテーブルからfamily が request.user.family の子どもだけに絞る = ログイン中のユーザーの家族に属する子どもだけを取得する
    children = Child.objects.filter(family=family).order_by("id")
    
    # ① ログイン中ユーザーの個人カラーを取得する
    my_color_hex = None

    # request.user に対応する色設定を探す
    my_assignment = FamilyColorAssignment.objects.filter(
        user=request.user
    ).first()

    # 色設定が見つかったら、color_code から実際のHEXカラーを取り出す
    if my_assignment:
        my_color_hex = COLOR_HEX_MAP.get(my_assignment.color_code)
    
    # 家族の合同予定カラーを取得する
    shared_color_hex = None
    
    shared_assignment = FamilyColorAssignment.objects.filter(
        family=family,
        assign_type=FamilyColorAssignment.AssignType.SHARED,
    ).first()

    if shared_assignment:
        shared_color_hex = COLOR_HEX_MAP.get(shared_assignment.color_code)
    
    # ② 大人メンバー一覧に、表示用の色を付ける
    # テンプレートで使いやすいように、
    # 各 user オブジェクトに color_hex という属性を追加する
    for member in adult_members:
        member.color_hex = None

        # その大人メンバーの色設定を探す
        assignment = FamilyColorAssignment.objects.filter(
            user=member
        ).first()

        # 色設定があれば HEXカラーに変換して持たせる
        if assignment:
            member.color_hex = COLOR_HEX_MAP.get(assignment.color_code)
            
    # ③ 子どもメンバー一覧にも、表示用の色を付ける
    for child in children:
        # まずは未設定にしておく
        child.color_hex = None

        # その子どもの色設定を探す
        assignment = FamilyColorAssignment.objects.filter(
            child=child
        ).first()

        # 色設定があれば HEXカラーに変換して持たせる
        if assignment:
            child.color_hex = COLOR_HEX_MAP.get(assignment.color_code)

    context = {
        "family": family,
        "adult_members": adult_members,
        "children": children,
        "my_color_hex": my_color_hex,
        "shared_color_hex": shared_color_hex,
    }
    
    return render(
        request, 
        "families/family_settings.html",
        context
    )

@login_required
def family_profile_edit_view(request):
    family = request.user.family
    
    if request.method == "POST":
        # もともとの古い画像（保存前の画像）を覚えておく
        old_image = family.image
        
        # 送信された内容で既存の家族データを更新するためのフォームを作る
        form = FamilyProfileForm(request.POST, request.FILES, instance=family)
        if form.is_valid():
            # フォームで選んだ合同予定カラーを取り出す
            color_code = form.cleaned_data["color_code"]
            
            # 今回新しく画像が選ばれたか確認する
            new_image = form.cleaned_data.get("image")

            try:
                # Familyの更新と合同予定カラーの更新を
                # 「全部成功するか、全部やめるか」でまとめる
                with transaction.atomic():
                    # ① Family本体を保存
                    # （name, image）
                    form.save()

                    # ② 合同予定カラーを保存
                    # 1家族につき1件だけ持たせる
                    FamilyColorAssignment.objects.update_or_create(
                        family=family,
                        assign_type=FamilyColorAssignment.AssignType.SHARED,
                        defaults={
                            "user": None,   # 合同予定カラーなので user は空
                            "child": None,  # 合同予定カラーなので child は空
                            "color_code": color_code,
                        }
                    )
            
                # 新しい画像が送られたときだけ差し替え後に古い画像を削除
                # 新しい画像が送られた、もともと古い画像があった、保存後に画像が変わった、この3つを満たしたときだけ古いファイルを削除
                if new_image and old_image and old_image != family.image:
                    old_image.delete(save=False)
                
                return redirect("families:family_settings")
    
            except IntegrityError:
                # 同じ家族内で、すでに他の大人や子どもが使っている色を
                # 合同予定カラーとして選んだときなど
                form.add_error(
                    "color_code",
                    "この色はすでに家族内で使われています。別の色を選択してください"
                )
                
    # form = FamilyProfileForm()は新しくfamilyを作るためのフォーム。instanceなしは白紙の申請書を渡されるイメージ
    # form = FamilyProfileForm(instance=family)はすでにあるfamilyを編集するためのフォーム。instanceありはすでに記入済みの申請書を渡されるイメージ
    # request.user.family（＝ログイン中ユーザーの家族データ）を使って編集用フォームを作り、フォームに最初から値を入れて表示
    else:
        form = FamilyProfileForm(instance=family)
         
    return render(
        request,
        "families/family_profile_edit.html",
        {"form": form, "family": family},
    )
    
@login_required
def setup_completed_view(request):
    """
    家族設定登録完了画面

    条件
    - 初期設定が完了していること
    - そのユーザーがまだこの画面を見ていないこと

    この画面を表示したら、
    「見た」というフラグを True にする
    """

    user = request.user

    # 初期設定が未完了なら、この画面は表示しない
    # 苗字の設定画面へ戻す
    if not is_initial_setup_completed(user):
        return redirect("families:family_profile_edit")

    # すでに完了画面を見たユーザーなら、
    # 何度も表示せず、家族設定画面へ戻す
    if user.has_seen_family_setup_completed:
        return redirect("families:family_settings")

    # ここまで来たら、初めて完了画面を表示してよいユーザー
    # 「もう見た」に更新して保存する
    user.has_seen_family_setup_completed = True
    user.save(update_fields=["has_seen_family_setup_completed"])

    return render(request, "families/setup_completed.html")          
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import FamilyProfileForm
from children.models import Child
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def family_settings_view(request):
    # ログインしているユーザー(request.user)の家族を取り出してfamily という変数に入れる
    family = request.user.family
    # ログイン中のユーザーの家族に属する大人だけを取得する
    adult_members = User.objects.filter(family=family).order_by("id")
    # children_childテーブルからfamily が request.user.family の子どもだけに絞る = ログイン中のユーザーの家族に属する子どもだけを取得する
    children = Child.objects.filter(family=family).order_by("id")
    
    return render(
        request, 
        "families/family_settings.html",
        {
            "family": family,
            "adult_members": adult_members,
            "children": children,
        },
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
            # 今回新しく画像が選ばれたか確認する
            new_image = form.cleaned_data.get("image")

            form.save()
            
            # 新しい画像が送られたときだけ差し替え後に古い画像を削除
            # 新しい画像が送られた、もともと古い画像があった、保存後に画像が変わった、この3つを満たしたときだけ古いファイルを削除
            if new_image and old_image and old_image != family.image:
                old_image.delete(save=False)
                
            return redirect("families:family_settings")
    
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
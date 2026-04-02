# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

import os

class User(AbstractUser):
    # username（ユーザー名）を使わず、emailをログインIDにしたいので消す。Django標準Userが持つ username 欄を使わない宣言
    username = None 
    
    # email をログインIDとして使う（unique=True で重複登録を禁止）
    email = models.EmailField(
        unique=True,
    ) 
    
    family = models.ForeignKey(
        "families.Family", # 文字列参照。参照先（アプリ名.モデル名）= familiesアプリのFamilyモデルを参照。
        on_delete=models.PROTECT, # CASCADE:親（Family）を消したら子（User）も一緒に消えるだと困る
        null=True, # DBでNULL許可
        blank=True, # フォーム入力で空を許可
        related_name="users", # 逆参照名
    )
    
    name = models.CharField(
        max_length=30,
    )
    
    # ImageField：画像ファイルをアップロードして保存するためのフィールド（画像ファイルを受け取る。保存する。画像のパスをDBに保存する）
    image = models.ImageField(
        upload_to="users/",   # media/users/ に保存される          
    )

    # 作成日時は AbstractUser の date_joined を使う
    # 更新日時
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    # 家族設定登録完了画面を、すでに見たかどうか
    # False = まだ見ていない
    # True = もう見た
    has_seen_family_setup_completed = models.BooleanField(
        default=False,
    )
    
    # Djangoに「ログインIDはemailだよ」と教える
    USERNAME_FIELD = "email"
    # createsuperuser を作るときに USERNAME_FIELD 以外で「必須として聞く項目」を指定するリスト。createsuperuser 実行時に Email と Passwordだけ聞かれる 
    REQUIRED_FIELDS = [] 
    
    def __str__(self):
        return self.name or self.email
    
    def save(self, *args, **kwargs):
        """
        画像が変更されたときに、前の画像ファイルを削除する

        やりたい動き：
        - 新しい画像を選ばず保存 → 今の画像をそのまま使う
        - 新しい画像を選んで保存 → 古い画像を削除して差し替える
        """
        old_image_path = None

        # すでにDBに存在するユーザー（編集時）のときだけ、
        # 以前の画像を調べる
        if self.pk:
            old_user = User.objects.filter(pk=self.pk).first() # 今保存しようとしているユーザーの、DBに入っている元のデータを取っている

            # 以前の画像があり、
            # かつ今回の画像と違うときだけ削除候補にする
            if old_user and old_user.image and old_user.image != self.image: # old_user.image != self.image は前の画像と今回の画像が違うかどうか
                old_image_path = old_user.image.path

        # まず通常どおり保存する
        # 先に保存しておくことで、保存失敗時に古い画像まで消える事故を防げる
        super().save(*args, **kwargs)

        # 保存後、古い画像ファイルがあって、実際に存在していれば削除する
        if old_image_path and os.path.isfile(old_image_path):
            os.remove(old_image_path)

    def delete(self, *args, **kwargs):
        """
        ユーザー自体を削除したときに、画像ファイルも削除する
        """
        image_path = None

        # 画像があるなら、削除前にパスを控えておく
        if self.image:
            image_path = self.image.path
            
        # 先にDBのユーザーを削除
        super().delete(*args, **kwargs)
        
        # 実ファイルが残っていれば削除
        if image_path and os.path.isfile(image_path):
            os.remove(image_path)
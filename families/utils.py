# families/utils.py
from color_assignments.models import FamilyColorAssignment

def is_initial_setup_completed(user):
    """
    初期設定が完了しているかを判定する関数

    判定条件
    - 家族名が入っている
    - 合同予定カラーが保存されている

    返り値
    - 完了している → True
    - 未完了 → False
    """
    family = user.family

    # user に family がなければ未完了
    if not user.family:
        return False

    # 家族名が入っているか
    # signup直後は family.name = "" のことがある
    # strip() を使うと、空白だけの入力も未設定扱いにできる
    has_family_name = bool(family.name and family.name.strip())

    # 合同予定カラーが保存されているか
    shared_assignment = FamilyColorAssignment.objects.filter(
        family=family,
        assign_type=FamilyColorAssignment.AssignType.SHARED,
    ).first()

    has_shared_color = shared_assignment is not None

    # 家族名あり かつ 合同予定カラーあり なら完了
    return has_family_name and has_shared_color
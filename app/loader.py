import json
from pathlib import Path

from app.models import UserActivity, HRContext, AccessPrivilege


def load_user_activities(file_path: str) -> list[UserActivity]:
    """
    ユーザーアクティビティの JSON ファイルを読み込み、
    UserActivity のリストとして返す。
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    activities = [UserActivity(**item) for item in raw_data]
    return activities


def load_hr_contexts(file_path: str) -> dict[str, HRContext]:
    """
    HR コンテキストの JSON ファイルを読み込み、
    user_id をキーとする HRContext の辞書として返す。
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    hr_contexts = {item["user_id"]: HRContext(**item) for item in raw_data}
    return hr_contexts


def load_access_privileges(file_path: str) -> dict[str, AccessPrivilege]:
    """
    アクセス権限の JSON ファイルを読み込み、
    user_id をキーとする AccessPrivilege の辞書として返す。
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    access_privileges = {
        item["user_id"]: AccessPrivilege(**item) for item in raw_data
    }
    return access_privileges
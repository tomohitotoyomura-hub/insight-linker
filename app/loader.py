import json
from pathlib import Path

from app.models import UserActivity, HRContext, AccessPrivilege


def load_user_activities(file_path: str) -> list[UserActivity]:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    activities = [UserActivity(**item) for item in raw_data]
    return activities


def load_hr_contexts(file_path: str) -> dict[str, HRContext]:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    hr_contexts = {item["user_id"]: HRContext(**item) for item in raw_data}
    return hr_contexts


def load_access_privileges(file_path: str) -> dict[str, AccessPrivilege]:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    access_privileges = {
        item["user_id"]: AccessPrivilege(**item) for item in raw_data
    }
    return access_privileges
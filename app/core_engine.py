from datetime import datetime

from app.models import (
    UserActivity,
    HRContext,
    AccessPrivilege,
    EvaluationResult,
)


def is_after_hours(timestamp: str) -> bool:
    """
    対象の timestamp が時間外（22:00〜05:59）かどうかを判定する。
    """
    hour = int(timestamp[11:13])
    return hour < 6 or hour >= 22


def is_allowed_resource(resource_path: str, allowed_resources: list[str]) -> bool:
    """
    アクセス先 resource_path が、許可されたパスプレフィックス群に含まれているかを判定する。
    """
    return any(resource_path.startswith(prefix) for prefix in allowed_resources)


def evaluate_activity(
    activity: UserActivity,
    hr_contexts: dict[str, HRContext],
    access_privileges: dict[str, AccessPrivilege],
) -> EvaluationResult:
    """
    1件のユーザーアクティビティについて、
    HR コンテキストと権限情報を突き合わせてリスク評価を行い、
    EvaluationResult として返す。
    """

    user_id = activity.user_id
    hr = hr_contexts.get(user_id)
    privilege = access_privileges.get(user_id)

    # 元イベントに対する簡易な一意 ID（MVP では timestamp + user_id + action で生成）
    event_id = f"{activity.timestamp}-{activity.user_id}-{activity.action}"

    # 評価メタ情報（いつ・どのスコアリングプロファイルで評価したか）
    evaluated_at = datetime.now().isoformat(timespec="seconds")
    scoring_profile = "MVP_v1_3rules"

    # リスク評価用の一時変数
    risk_score = 0
    reasons: list[str] = []
    rule_hits: list[str] = []

    # ロバストネス・品質フラグ（コンテキスト欠損などを記録する）
    has_missing_hr = hr is None
    has_missing_privilege = privilege is None
    error_flags: list[str] = []

    # HR 情報が無い・権限情報が無い場合は、その旨を error_flags に記録
    # （MVP ではスコアには反映せず、品質の注意点として扱う）
    if has_missing_hr:
        error_flags.append("MISSING_HR_CONTEXT")
    if has_missing_privilege:
        error_flags.append("MISSING_ACCESS_PRIVILEGE")

    # ルール1: 休暇中アクセス
    if hr and hr.is_on_leave:
        risk_score += 2
        reasons.append("Access during leave")
        rule_hits.append("ON_LEAVE_ACCESS")

    # ルール2: 退職通知済み + 時間外アクセス
    if hr and hr.resignation_notified and is_after_hours(activity.timestamp):
        risk_score += 3
        reasons.append("After-hours access by resignation-notified user")
        rule_hits.append("AFTER_HOURS_RESIGNATION_ACCESS")

    # ルール3: 許可外リソースアクセス
    if privilege and not is_allowed_resource(
        activity.resource_path, privilege.allowed_resources
    ):
        risk_score += 3
        reasons.append("Access to unauthorized resource")
        rule_hits.append("UNAUTHORIZED_RESOURCE_ACCESS")

    # スコアからリスクレベルを決定
    if risk_score >= 5:
        risk_level = "High"
    elif risk_score >= 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Medium / High を「要フォロー」とみなす
    is_suspicious = risk_level in {"Medium", "High"}

    return EvaluationResult(
        # 元イベント情報
        event_id=event_id,
        timestamp=activity.timestamp,
        user_id=activity.user_id,
        action=activity.action,
        resource_path=activity.resource_path,
        # 評価メタ情報
        evaluated_at=evaluated_at,
        scoring_profile=scoring_profile,
        data_version=None,
        # リスク評価情報
        risk_score=risk_score,
        risk_level=risk_level,
        reasons=reasons,
        rule_hits=rule_hits,
        # ロバストネス・品質フラグ
        is_suspicious=is_suspicious,
        has_missing_hr=has_missing_hr,
        has_missing_privilege=has_missing_privilege,
        error_flags=error_flags,
    )
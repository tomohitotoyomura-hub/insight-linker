from dataclasses import dataclass, field
from typing import List


@dataclass
class UserActivity:
    """
    SIEM やログ管理システムから取得したユーザーアクティビティの 1 イベント分。
    MVP では timestamp は文字列、resource_path は単純なパス文字列として扱う。
    """
    timestamp: str
    user_id: str
    action: str
    resource_path: str


@dataclass
class HRContext:
    """
    人事システム由来のコンテキスト情報。
    休暇中かどうか、退職通知済みかどうか、所属部署などを表す。
    """
    user_id: str
    is_on_leave: bool
    resignation_notified: bool
    department: str


@dataclass
class AccessPrivilege:
    """
    権限管理（例: AD）の情報。
    ユーザーの権限レベルと、アクセスを許可されたリソースパスの一覧。
    """
    user_id: str
    privilege_level: str
    allowed_resources: List[str]


@dataclass
class EvaluationResult:
    """
    Insight-Linker における 1 イベント分のリスク評価結果を表すモデル。

    - event_* : 元の行動イベントの情報
    - evaluated_* / scoring_* : 評価がいつ・どのロジックで行われたか
    - risk_* : リスクスコアとレベル
    - *_flags : データ欠損や注意すべき前提条件
    """
    # 元イベント情報
    event_id: str
    timestamp: str
    user_id: str
    action: str
    resource_path: str

    # 評価メタ情報
    evaluated_at: str
    scoring_profile: str  # 例: "MVP_v1_3rules"
    data_version: str | None = None

    # リスク評価情報
    risk_score: int = 0
    risk_level: str = "Low"  # "Low" / "Medium" / "High"
    reasons: List[str] = field(default_factory=list)
    rule_hits: List[str] = field(default_factory=list)

    # ロバストネス・品質フラグ
    is_suspicious: bool = False
    has_missing_hr: bool = False
    has_missing_privilege: bool = False
    error_flags: List[str] = field(default_factory=list)
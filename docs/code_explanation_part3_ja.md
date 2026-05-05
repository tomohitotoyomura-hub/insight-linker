##1. Part3 の目的と位置づけ

このログは、Insight-Linker MVP の Day6-Day8 終了時点で新たに追加・更新された主要ソースファイルについて、
「そのコードが何をしているのか」を後から自分で理解し直せるようにするために作成したものである。
「何をしているか」だけでなく、「なぜその処理が必要なのか」「なぜこの設計にしたのか」まで残すことを意図している。

このドキュメントは、Insight-Linker MVP の開発過程で作成した個人用の学習ログを兼ねた設計メモです。
将来的に英語ドキュメントへ発展させるための下書きという位置付けです。

Part1 / Part2 では、主に
・Day3: main.py / models.py / loader.py と JSON 入力
・Day4: core_engine.py による 3 ルールのイベント単位スコアリング
・Day5: report_gen.py による Markdown レポート生成と main.py での統合
までを整理した。

Part3 では、その続きとして

・Day6: EvaluationResult dataclass の導入と、イベント評価の構造化
・Day7: day7_analysis.py によるセッション単位・ユーザー単位のリスク集計
・Day8: Day7 結果を Markdown レポートへ統合する report_gen.py の拡張
についてコードレベルでまとめる。

##2. Day6: EvaluationResult dataclass の導入
###2-1. Day5 までの課題
Day5 までは、core_engine.evaluate_activity() の戻り値は素の dict で、例えば以下のような形だった。

python
return {
    "user_id": activity.user_id,
    "timestamp": activity.timestamp,
    "action": activity.action,
    "resource_path": activity.resource_path,
    "risk_level": risk_level,
    "risk_score": risk_score,
    "reasons": reasons,
}
この形でも動くが、
・フィールドが増えたときにキー名の typo に気付きにくい
・呼び出し側で型補完が効きにくい
・レポート生成側での扱いが「dict 前提」になり、拡張時にバラバラになりやすい
という問題があった。
そこで Day6 では、評価結果を 1 つの dataclass で表現する EvaluationResult を追加した。

###2-2. app/models.py における EvaluationResult
app/models.py には、既存の 3 つのドメインモデルに加えて、EvaluationResult を定義している。

python
from dataclasses import dataclass, field
from typing import List

@dataclass
class EvaluationResult:
    # 元イベント情報
    event_id: str
    timestamp: str
    user_id: str
    action: str
    resource_path: str

    # 評価メタ情報
    evaluated_at: str
    scoring_profile: str
    data_version: str | None = None

    # リスク評価情報
    risk_score: int = 0
    risk_level: str = "Low"
    reasons: List[str] = field(default_factory=list)
    rule_hits: List[str] = field(default_factory=list)

    # ロバストネス・品質フラグ
    is_suspicious: bool = False
    has_missing_hr: bool = False
    has_missing_privilege: bool = False
    error_flags: List[str] = field(default_factory=list)
ポイントは次の通り。

元イベント情報: event_id, timestamp, user_id, action, resource_path
→ 元の UserActivity との対応を保つための情報。

評価メタ情報: evaluated_at, scoring_profile, data_version
→ いつ・どのロジックで評価したかを追跡するためのメタデータ。

リスク評価情報: risk_score, risk_level, reasons, rule_hits
→ スコア・ラベル・理由・どのルールに引っかかったか。

ロバストネスフラグ: is_suspicious, has_missing_hr, has_missing_privilege, error_flags
→ 「Medium/High かどうか」や、コンテキスト欠損の有無など、品質と注意点を表す。

これにより、評価結果が単なる dict ではなく「型付きのオブジェクト」として扱えるようになった。

###2-3. core_engine.evaluate_activity の修正
Day6 では、core_engine.evaluate_activity() の戻り値を dict から EvaluationResult に変えた。

python
from datetime import datetime
from app.models import (
    UserActivity,
    HRContext,
    AccessPrivilege,
    EvaluationResult,
)

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

    # 元イベントに対する簡易な一意 ID
    event_id = f"{activity.timestamp}-{activity.user_id}-{activity.action}"

    # 評価メタ情報
    evaluated_at = datetime.now().isoformat(timespec="seconds")
    scoring_profile = "MVP_v1_3rules"

    # リスク評価用の一時変数
    risk_score = 0
    reasons: list[str] = []
    rule_hits: list[str] = []

    # ロバストネス・品質フラグ
    has_missing_hr = hr is None
    has_missing_privilege = privilege is None
    error_flags: list[str] = []

    if has_missing_hr:
        error_flags.append("MISSING_HR_CONTEXT")
    if has_missing_privilege:
        error_flags.append("MISSING_ACCESS_PRIVILEGE")

    # 休暇中アクセス
    if hr and hr.is_on_leave:
        risk_score += 2
        reasons.append("Access during leave")
        rule_hits.append("ON_LEAVE_ACCESS")

    # 退職通知済み + 時間外アクセス
    if hr and hr.resignation_notified and is_after_hours(activity.timestamp):
        risk_score += 3
        reasons.append("After-hours access by resignation-notified user")
        rule_hits.append("AFTER_HOURS_RESIGNATION_ACCESS")

    # 許可外リソースアクセス
    if privilege and not is_allowed_resource(
        activity.resource_path, privilege.allowed_resources
    ):
        risk_score += 3
        reasons.append("Access to unauthorized resource")
        rule_hits.append("UNAUTHORIZED_RESOURCE_ACCESS")

    # リスクレベル判定
    if risk_score >= 5:
        risk_level = "High"
    elif risk_score >= 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    is_suspicious = risk_level in {"Medium", "High"}

    return EvaluationResult(
        event_id=event_id,
        timestamp=activity.timestamp,
        user_id=activity.user_id,
        action=activity.action,
        resource_path=activity.resource_path,
        evaluated_at=evaluated_at,
        scoring_profile=scoring_profile,
        data_version=None,
        risk_score=risk_score,
        risk_level=risk_level,
        reasons=reasons,
        rule_hits=rule_hits,
        is_suspicious=is_suspicious,
        has_missing_hr=has_missing_hr,
        has_missing_privilege=has_missing_privilege,
        error_flags=error_flags,
    )
ルール自体（3ルール）は Day5 と変えていない が、
結果の表現を EvaluationResult にしたことで、後続のレポート生成・集計での扱いやすさが大きく向上した。

##3. Day7: day7_analysis.py によるセッション／ユーザー単位分析
###3-1. Day7 で追加されたサンプル CSV ログ
Day7 では、既存の JSON ベース event-level 評価とは別に、
セッション分析用のサンプル CSV data/day7_sample_logs.csv を追加した。

この CSV は行動系列の分析用で、各行は次のような情報を持つ想定。

・timestamp: イベント時刻（UTC）
・user_id: ユーザーID
・action: login / read / download / change_permission / logout など
・resource: 対象リソースパス（/restricted/ を含むかどうかを判定）
・result: success / denied など

Day7 は「セッション」という単位で行動を見るためのレイヤーであり、
Day1〜Day6 の JSON ベース評価とは別のサンプル入力を使っている。

###3-2. day7_analysis.py の役割
day7_analysis.py は、Day7 専用のセッション分析ロジックをまとめたモジュールで、
主に以下の役割を持つ。

・CSV ログの読み込みと前処理 (load_logs)
・user_id ごとのセッション分割 (assign_session_ids)
・セッション単位のスコアリング (score_session)
・セッション／ユーザー単位の集計テーブル作成 (build_session_risk_table, build_user_risk_table)
・一連の流れをまとめた run_day7_analysis()

###3-3. ログ読み込みとセッションID付与
まず CSV ログを DataFrame に読み込むのが load_logs()。

python
def load_logs(csv_path: str) -> pd.DataFrame:
    """
    Day7 用のサンプルログ CSV を読み込み、前処理した DataFrame を返す。
    """
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    return df
続いて、30 分以上の無操作でセッションを分割するのが assign_session_ids()。

python
SESSION_GAP_SECONDS = 30 * 60  # 30分

def assign_session_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    user_id ごとに連続するイベントをまとめ、
    30 分以上の無操作があれば新しい session_id を振る。
    """
    time_diff = df.groupby("user_id")["timestamp"].diff().dt.total_seconds()
    new_session_flag = time_diff.isna() | (time_diff >= SESSION_GAP_SECONDS)

    df["session_id"] = (
        new_session_flag.groupby(df["user_id"]).cumsum() - 1
    ).astype(int)

    df = df.sort_values(["user_id", "session_id", "timestamp"]).reset_index(drop=True)
    return df
これにより、同じ user_id の中で 30分以上空いたタイミングでセッションが切り替わる。

###3-4. セッションスコアリングルール
Day7 のセッション単位スコアリングは score_session() に集約されている。

ルールは以下の通り。

・深夜イベントあり（22:00〜05:59 JST） → +2 (night_time(+2))
・/restricted/ を含む resource あり → +2 (restricted_resource(+2))
・restricted リソースの download あり → +3 (restricted_download(+3))
・change_permission あり → +3 (change_permission(+3))

result == "denied" が1件以上 → +1 (denied_once(+1))

result == "denied" が2件以上 → +2 (denied_multiple(+2))

深夜判定は JST ベースで行う。

python
NIGHT_START = 22
NIGHT_END = 5  # 0〜5時台を深夜とみなす

def is_night(ts: pd.Timestamp) -> bool:
    """
    対象の時刻が深夜時間帯 (22:00〜05:59 JST) かどうかを判定する。
    """
    hour = ts.tz_convert("Asia/Tokyo").hour if ts.tzinfo is not None else ts.hour
    return (hour >= NIGHT_START) or (hour <= NIGHT_END)
スコアからのリスクレベルはシンプルに

・score >= 6 → High
・score >= 3 → Medium
・それ以外 → Low
と決めている。

###3-5. セッションリスクテーブルとユーザーリスクテーブル
セッション単位の集計を行うのが build_session_risk_table()。

python
def build_session_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    全セッションについて score_session を適用し、
    セッション単位のリスクテーブルを DataFrame として返す。
    """
    rows = []
    for (_, _), group in df.groupby(["user_id", "session_id"]):
        rows.append(score_session(group))

    session_risk_df = pd.DataFrame(rows)

    risk_rank = {"High": 2, "Medium": 1, "Low": 0}
    session_risk_df["risk_rank"] = session_risk_df["risk_level"].map(risk_rank)

    session_risk_df = (
        session_risk_df.sort_values(
            ["risk_rank", "score", "user_id", "session_id"],
            ascending=[False, False, True, True],
        )
        .drop(columns=["risk_rank"])
        .reset_index(drop=True)
    )

    return session_risk_df
ユーザー単位の集計は build_user_risk_table() で行い、

・final_risk_level: そのユーザーで最も高いセッションリスク
・total_score: 全セッションスコア合計
・session_count: セッション数
・high_session_count / medium_session_count / low_session_count
を計算する。

python
def build_user_risk_table(session_risk_df: pd.DataFrame) -> pd.DataFrame:
    """
    各ユーザーについて、セッション結果を集約しユーザー単位のリスクテーブルを返す。
    """
    risk_order = {"Low": 0, "Medium": 1, "High": 2}
    inv_map = {v: k for k, v in risk_order.items()}

    def _agg(group: pd.DataFrame) -> pd.Series:
        max_level_num = group["risk_level"].map(risk_order).max()
        final_level = inv_map[max_level_num]

        return pd.Series(
            {
                "final_risk_level": final_level,
                "total_score": group["score"].sum(),
                "session_count": len(group),
                "high_session_count": (group["risk_level"] == "High").sum(),
                "medium_session_count": (group["risk_level"] == "Medium").sum(),
                "low_session_count": (group["risk_level"] == "Low").sum(),
            }
        )

    user_risk_df = session_risk_df.groupby("user_id").apply(_agg).reset_index()

    user_risk_df["risk_rank"] = user_risk_df["final_risk_level"].map(risk_order)
    user_risk_df = (
        user_risk_df.sort_values(
            ["risk_rank", "total_score"],
            ascending=[False, False],
        )
        .drop(columns=["risk_rank"])
        .reset_index(drop=True)
    )

    return user_risk_df
###3-6. run_day7_analysis と main.py 統合
Day7 では、最後に run_day7_analysis() を用意し、main.py から呼び出すようにした。

python
def run_day7_analysis(csv_path: str = "data/day7_sample_logs.csv"):
    """
    Day7 の分析フローを一括で実行し、
    元ログ・セッション単位リスク・ユーザー単位リスクを返す。
    """
    df = load_logs(csv_path)
    df = assign_session_ids(df)

    session_risk_df = build_session_risk_table(df)
    user_risk_df = build_user_risk_table(session_risk_df)

    print("=== Session-level risk ===")
    print(session_risk_df.to_string(index=False))

    print("\n=== User-level risk ===")
    print(user_risk_df.to_string(index=False))

    return df, session_risk_df, user_risk_df
main.py からは、Day1〜Day6 の event-level 評価のあとに run_day7_analysis() を呼び出し、
Session-level / User-level risk が続けて表示される構成になっている。

##4. Day8: report_gen.py によるレポート拡張（Session/User テーブル）
###4-1. Day8 の狙い
Day7 でセッション／ユーザー単位の分析はできるようになったが、
結果はコンソールにしか出ておらず、Markdown レポートには反映されていなかった。

Day8 ではこれを解消し、

・event-level の Summary / High / Medium Findings
・Session-level の Summary / 詳細テーブル
・User-level の Summary / 詳細テーブル
を 1 枚の Markdown レポートにまとめることを目標にした。

###4-2. build_markdown_report のシグネチャ拡張
build_markdown_report() を、Day7 の結果 DataFrame を受け取れる形に拡張した。

python
import pandas as pd
from typing import List, Optional

def build_markdown_report(
    results: List[EvaluationResult],
    session_risk_df: Optional[pd.DataFrame] = None,
    user_risk_df: Optional[pd.DataFrame] = None,
) -> str:
    ...
results: EvaluationResult のリスト（event-level）

session_risk_df: セッション単位テーブル（Day7）

user_risk_df: ユーザー単位テーブル（Day7）

###4-3. event-level 部分はそのまま維持
Summary / High Risk Findings / Medium Risk Findings の構成は Day6 と同じで、
Total 件数や百分率の計算ロジックも変えていない。

これにより、Day8 の変更によって既存の挙動・見え方が崩れないようにした。

###4-4. Session Risk Summary セクションの追加
session_risk_df が渡されている場合、以下の内容を出力する。

text
## Session Risk Summary

- Total sessions: 4
- High risk sessions: 1
- Medium risk sessions: 1
- Low risk sessions: 2

### Session details

| user_id | session_id | risk_level | score | event_count | duration_seconds | session_start (UTC)        | session_end (UTC)          | reasons |
|--------|-----------:|-----------|------:|------------:|-----------------:|----------------------------|----------------------------|---------|
| u001 | 1 | High | 7 | 2 | 68 | 2026-05-04T14:48:02+00:00 | 2026-05-04T14:49:10+00:00 | night_time(+2), restricted_resource(+2), denied_once(+1), denied_multiple(+2) |
| u002 | 0 | Medium | 5 | 3 | 222 | 2026-05-04T14:50:45+00:00 | 2026-05-04T14:54:27+00:00 | night_time(+2), change_permission(+3) |
| u001 | 0 | Low | 0 | 3 | 318 | 2026-05-04T00:00:15+00:00 | 2026-05-04T00:05:33+00:00 | None |
| u003 | 0 | Low | 0 | 3 | 305 | 2026-05-04T01:15:00+00:00 | 2026-05-04T01:20:05+00:00 | None |
session_start / session_end は UTC として出力し、ヘッダに (UTC) と明記。

reasons は Day7 の score_session() が生成した文字列をそのまま使用。

###4-5. User Risk Summary セクションの追加
user_risk_df が渡されている場合、以下の内容を出力する。

text
## User Risk Summary

- Total users in Day7 analysis: 3
- Users with final High risk: 1
- Users with final Medium risk: 1
- Users with final Low risk: 1

### User details

| user_id | final_risk_level | total_session_score | session_count | high_sessions | medium_sessions | low_sessions |
|--------|------------------|--------------------:|--------------:|--------------:|----------------:|-------------:|
| u001 | High | 7 | 2 | 1 | 0 | 1 |
| u002 | Medium | 5 | 1 | 0 | 1 | 0 |
| u003 | Low | 0 | 1 | 0 | 0 | 1 |
###4-6. Notes の追記（UTC / 別サンプル説明）
Notes セクションには、次の3行を追加した。

text
- Day7 session start/end timestamps are handled as UTC (sample CSV is stored in UTC).
- Event-level JSON and Day7 CSV are separate sample datasets used for different layers of the MVP.
- Day7 session-level and user-level analysis is included when sample log data is available.
これにより、

セッション時刻表示が UTC であること

・event-level と Day7 analysis が別サンプルセットを使っていること
・Day7 部分がオプション的な追加レイヤーであること
を明示できるようになった。

##5. まとめ（Day6〜Day8 のコード構造）
Day6:

・EvaluationResult dataclass により、イベント評価結果を構造化
・core_engine.evaluate_activity() が EvaluationResult を返すように変更
レポート生成・コンソール出力のベースが「型付き」になり、拡張しやすくなった。

Day7:

・day7_analysis.py でセッション／ユーザー単位のリスク分析を追加
・CSV ベースのサンプルログから、セッション分割 (assign_session_ids)、セッションスコアリング (score_session)、
・ユーザー集計 (build_user_risk_table) を実装
main.py から Day7 分析を呼び出すことで、python main.py 1 回で event-level / session-level / user-level を確認可能にした。

Day8:

・report_gen.py を拡張し、Day7 の session_risk_df / user_risk_df を Markdown レポートに統合
・Session / User の詳細は Markdown テーブルで表現し、Notes で UTC／別サンプルを説明
・README の Sample console output / Sample report output を Day8 仕様に同期させた。
この3日間の実装により、Insight-Linker は

単発イベントのルールベース判定（Day1〜Day5）
セッションとしての行動パターン分析（Day7）
ユーザー単位のリスク集約とレポートへの一体出力（Day8）
という3層構造を持つ小さな MVP として整理された。
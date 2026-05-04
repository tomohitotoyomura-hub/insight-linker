from pathlib import Path
from datetime import datetime
from typing import List, Optional

import pandas as pd  # Day8: テーブル出力のために利用

from app.models import EvaluationResult


def _format_iso(dt: Optional[datetime]) -> str:
    """
    datetime っぽい値を ISO 文字列に整形するヘルパー。
    pandas の Timestamp / None / 文字列などを安全に文字列化する。
    """
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        return dt
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def build_markdown_report(
    results: List[EvaluationResult],
    session_risk_df: Optional[pd.DataFrame] = None,
    user_risk_df: Optional[pd.DataFrame] = None,
) -> str:
    """
    イベント単位の EvaluationResult と、
    Day7 のセッション／ユーザー単位リスク集計結果をもとに
    Insight-Linker の Markdown レポートを構築する。
    """
    # ===== Day1〜Day6: アクティビティ単位の集計 =====
    total_count = len(results)
    high_results = [r for r in results if r.risk_level == "High"]
    medium_results = [r for r in results if r.risk_level == "Medium"]
    low_results = [r for r in results if r.risk_level == "Low"]

    high_pct = round((len(high_results) / total_count) * 100) if total_count else 0
    medium_pct = round((len(medium_results) / total_count) * 100) if total_count else 0
    low_pct = round((len(low_results) / total_count) * 100) if total_count else 0

    unique_users = len({r.user_id for r in results}) if results else 0

    # 対象期間はイベントログ側の timestamp をもとに算出（sample data 前提）
    timestamps = [r.timestamp for r in results if r.timestamp]
    target_period = "N/A"
    if timestamps:
        try:
            min_date = min(ts[:10] for ts in timestamps)
            max_date = max(ts[:10] for ts in timestamps)
            target_period = min_date if min_date == max_date else f"{min_date} to {max_date}"
        except Exception:
            target_period = "sample data"

    lines: list[str] = []

    # ===== レポートヘッダ =====
    lines.append("# Insight-Linker Risk Report")
    lines.append("")
    lines.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Target period: {target_period} (sample data)")
    lines.append(f"Unique users: {unique_users}")
    lines.append("Scoring profile: MVP v1 (3 rules: leave status, resignation notice, unauthorized access)")
    lines.append("")

    # ===== イベント単位サマリー =====
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total events: {total_count}")
    lines.append(f"- High risk events: {len(high_results)} ({high_pct}%)")
    lines.append(f"- Medium risk events: {len(medium_results)} ({medium_pct}%)")
    lines.append(f"- Low risk events: {len(low_results)} ({low_pct}%)")
    lines.append("")

    # ===== High Risk Findings =====
    if high_results:
        lines.append("## High Risk Findings")
        lines.append("")
        for result in high_results:
            lines.append(f"### User {result.user_id} / {result.timestamp}")
            lines.append(f"- Risk level: {result.risk_level}")
            lines.append(f"- Risk score: {result.risk_score}")
            lines.append(f"- Reasons: {', '.join(result.reasons) if result.reasons else 'None'}")
            lines.append("")

    # ===== Medium Risk Findings =====
    if medium_results:
        lines.append("## Medium Risk Findings")
        lines.append("")
        for result in medium_results:
            lines.append(f"### User {result.user_id} / {result.timestamp}")
            lines.append(f"- Risk level: {result.risk_level}")
            lines.append(f"- Risk score: {result.risk_score}")
            lines.append(f"- Reasons: {', '.join(result.reasons) if result.reasons else 'None'}")
            lines.append("")

    # ===== Day8追加: セッション単位の要約（テーブル形式） =====
    if session_risk_df is not None and not session_risk_df.empty:
        total_sessions = len(session_risk_df)
        high_sessions = len(session_risk_df[session_risk_df["risk_level"] == "High"])
        medium_sessions = len(session_risk_df[session_risk_df["risk_level"] == "Medium"])
        low_sessions = len(session_risk_df[session_risk_df["risk_level"] == "Low"])

        lines.append("## Session Risk Summary")
        lines.append("")
        lines.append(f"- Total sessions: {total_sessions}")
        lines.append(f"- High risk sessions: {high_sessions}")
        lines.append(f"- Medium risk sessions: {medium_sessions}")
        lines.append(f"- Low risk sessions: {low_sessions}")
        lines.append("")

        lines.append("### Session details")
        lines.append("")
        # テーブルヘッダ
        lines.append(
            "| user_id | session_id | risk_level | score | event_count | duration_seconds | session_start (UTC)        | session_end (UTC)          | reasons |"
        )
        lines.append(
            "|--------|-----------:|-----------|------:|------------:|-----------------:|----------------------------|----------------------------|---------|"
        )

        # 各セッション行をテーブル形式で出力
        for _, row in session_risk_df.iterrows():
            user_id = row["user_id"]
            session_id = row["session_id"]
            risk_level = row["risk_level"]
            score = int(row["score"])
            event_count = int(row["event_count"])
            duration = int(row["duration_seconds"])
            start = _format_iso(row["session_start"])
            end = _format_iso(row["session_end"])
            reasons = row["reasons"] if row["reasons"] else "None"

            lines.append(
                f"| {user_id} | {session_id} | {risk_level} | {score} | {event_count} | {duration} | {start} | {end} | {reasons} |"
            )

        lines.append("")

    # ===== Day8追加: ユーザー単位の要約（テーブル形式） =====
    if user_risk_df is not None and not user_risk_df.empty:
        total_users_day7 = len(user_risk_df)
        high_users = len(user_risk_df[user_risk_df["final_risk_level"] == "High"])
        medium_users = len(user_risk_df[user_risk_df["final_risk_level"] == "Medium"])
        low_users = len(user_risk_df[user_risk_df["final_risk_level"] == "Low"])

        lines.append("## User Risk Summary")
        lines.append("")
        lines.append(f"- Total users in Day7 analysis: {total_users_day7}")
        lines.append(f"- Users with final High risk: {high_users}")
        lines.append(f"- Users with final Medium risk: {medium_users}")
        lines.append(f"- Users with final Low risk: {low_users}")
        lines.append("")

        lines.append("### User details")
        lines.append("")
        # テーブルヘッダ
        lines.append(
            "| user_id | final_risk_level | total_session_score | session_count | high_sessions | medium_sessions | low_sessions |"
        )
        lines.append(
            "|--------|------------------|--------------------:|--------------:|--------------:|----------------:|-------------:|"
        )

        for _, row in user_risk_df.iterrows():
            user_id = row["user_id"]
            final_level = row["final_risk_level"]
            total_score = int(row["total_score"])
            session_count = int(row["session_count"])
            high_sessions = int(row["high_session_count"])
            medium_sessions = int(row["medium_session_count"])
            low_sessions = int(row["low_session_count"])

            lines.append(
                f"| {user_id} | {final_level} | {total_score} | {session_count} | {high_sessions} | {medium_sessions} | {low_sessions} |"
            )

        lines.append("")

    # ===== Notes =====
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is generated from the current MVP scoring logic.")
    lines.append("- Low risk events are counted in the summary but omitted from detailed event findings.")
    lines.append("- Data in this report is sample data for MVP verification.")
    lines.append("- Current event-level rules focus on leave status, resignation notice, and unauthorized resource access.")
    # Day8: UTC とサンプルセットの違いを明示
    lines.append("- Day7 session start/end timestamps are handled as UTC (sample CSV is stored in UTC).")
    lines.append("- Event-level JSON and Day7 CSV are separate sample datasets used for different layers of the MVP.")
    lines.append("- Day7 session-level and user-level analysis is included when sample log data is available.")

    return "\n".join(lines)


def save_markdown_report(report_text: str, output_path: str) -> None:
    """
    出力先ディレクトリがなければ作成し、UTF-8 で Markdown ファイルを書き出す。
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report_text, encoding="utf-8")
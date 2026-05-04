from pathlib import Path
from datetime import datetime
from typing import List

from app.models import EvaluationResult


def build_markdown_report(results: List[EvaluationResult]) -> str:
    total_count = len(results)
    high_results = [r for r in results if r.risk_level == "High"]
    medium_results = [r for r in results if r.risk_level == "Medium"]
    low_results = [r for r in results if r.risk_level == "Low"]

    # 対象ユーザー数（ユニーク user_id 数）
    unique_users = len({r.user_id for r in results})

    # 件数が0の場合のゼロ除算対策
    if total_count > 0:
        high_pct = round(len(high_results) / total_count * 100)
        medium_pct = round(len(medium_results) / total_count * 100)
        low_pct = round(len(low_results) / total_count * 100)
    else:
        high_pct = medium_pct = low_pct = 0

    lines = [
        "# Insight-Linker Risk Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "Target period: 2026-05-01 (sample data)",
        f"Unique users: {unique_users}",
        "Scoring profile: MVP v1 (3 rules: leave status, resignation notice, unauthorized access)",
        "",
        "## Summary",
        "",
        f"- Total events: {total_count}",
        f"- High risk events: {len(high_results)} ({high_pct}%)",
        f"- Medium risk events: {len(medium_results)} ({medium_pct}%)",
        f"- Low risk events: {len(low_results)} ({low_pct}%)",
        "",
    ]

    if high_results:
        lines.append("## High Risk Findings")
        lines.append("")
        for result in high_results:
            lines.extend([
                f"### User {result.user_id} / {result.timestamp}",
                f"- Risk level: {result.risk_level}",
                f"- Risk score: {result.risk_score}",
                f"- Reasons: {', '.join(result.reasons) if result.reasons else 'None'}",
                "",
            ])

    if medium_results:
        lines.append("## Medium Risk Findings")
        lines.append("")
        for result in medium_results:
            lines.extend([
                f"### User {result.user_id} / {result.timestamp}",
                f"- Risk level: {result.risk_level}",
                f"- Risk score: {result.risk_score}",
                f"- Reasons: {', '.join(result.reasons) if result.reasons else 'None'}",
                "",
            ])

    lines.extend([
        "## Notes",
        "",
        "- This report is generated from the current MVP scoring logic.",
        "- Low risk events are counted in the summary but omitted from detailed findings.",
        "- Data in this report is sample data for MVP verification.",
        "- Current rules focus on leave status, resignation notice, and unauthorized resource access.",
        "",
    ])

    return "\n".join(lines)


def save_markdown_report(report_text: str, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text, encoding="utf-8")
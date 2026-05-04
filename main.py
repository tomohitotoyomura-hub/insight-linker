from datetime import datetime

# 入力データ読み込み用の関数をimport
from app.loader import (
    load_user_activities,
    load_hr_contexts,
    load_access_privileges,
)

# 各アクティビティのリスク評価を行う関数をimport
from app.core_engine import evaluate_activity

# Markdownレポート生成と保存を行う関数をimport
from app.report_gen import build_markdown_report, save_markdown_report

# Day7: ユーザー／セッション単位リスク分析ロジックをimport
from day7_analysis import run_day7_analysis


def main() -> None:
    # ===== 入力データの読み込み =====
    user_activities = load_user_activities("data/raw/user_activity.json")
    hr_contexts = load_hr_contexts("data/raw/hr_context.json")
    access_privileges = load_access_privileges("data/raw/access_privileges.json")

    # セットアップ完了と読み込み件数の確認
    print("Insight-Linker MVP setup complete")
    print(f"Loaded user activities: {len(user_activities)}")
    print(f"Loaded HR contexts: {len(hr_contexts)}")
    print(f"Loaded access privileges: {len(access_privileges)}")
    print()

    # ===== アクティビティ単位の評価（従来の Day1〜Day6 相当） =====
    print("=== Evaluation Results (per activity) ===")

    # 全評価結果を後でMarkdownレポート化するために格納するリスト
    results = []

    # 各アクティビティを評価し、コンソール表示とレポート用リストへの保存を行う
    for activity in user_activities:
        result = evaluate_activity(activity, hr_contexts, access_privileges)
        results.append(result)
        print(
            f"user_id={result.user_id}, "
            f"timestamp={result.timestamp}, "
            f"risk_level={result.risk_level}, "
            f"risk_score={result.risk_score}, "
            f"reasons={result.reasons}"
        )

    print()  # 区切り

    # ===== Day7: ユーザー／セッション単位のリスク分析 =====
    # day7_sample_logs.csv を前提としたセッション分析・リスクスコアリングを実行
    # 戻り値は (元DataFrame, セッション単位リスク, ユーザー単位リスク)
    _, session_risk_df, user_risk_df = run_day7_analysis("data/day7_sample_logs.csv")

    # ここではコンソール出力は day7_analysis 側に任せている。
    # 将来的にレポート統合する場合は、user_risk_df / session_risk_df を
    # Markdown セクションに変換して report_text に追記することを想定。

    # ===== Markdownレポートの生成（現時点ではアクティビティ単位のみ） =====
    report_text = build_markdown_report(results)

    # TODO: Day7 の結果をレポートに統合する場合は、
    # ここで user_risk_df / session_risk_df から概要セクションを組み立てて
    # report_text に追記する想定:
    #
    # report_text += "\n\n" + build_day7_summary_section(user_risk_df, session_risk_df)

    # ===== レポートファイルの保存 =====
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/{timestamp_str}_insight_report.md"

    save_markdown_report(report_text, output_path)

    print()
    print(f"Markdown report generated: {output_path}")


if __name__ == "__main__":
    main()
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

# レポートファイル名に日時を付与するための標準ライブラリをimport
from datetime import datetime


def main() -> None:
    # 入力データの読み込み
    user_activities = load_user_activities("data/raw/user_activity.json")
    hr_contexts = load_hr_contexts("data/raw/hr_context.json")
    access_privileges = load_access_privileges("data/raw/access_privileges.json")

    # セットアップ完了と読み込み件数の確認
    print("Insight-Linker MVP setup complete")
    print(f"Loaded user activities: {len(user_activities)}")
    print(f"Loaded HR contexts: {len(hr_contexts)}")
    print(f"Loaded access privileges: {len(access_privileges)}")
    print()

    # 評価結果の見出しを表示
    print("=== Evaluation Results ===")

    # 全評価結果を後でMarkdownレポート化するために格納するリストを用意
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

    # 評価結果リストからMarkdown形式のレポート本文を生成
    report_text = build_markdown_report(results)

    # 現在日時からレポート保存用のタイムスタンプ文字列を作成
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # タイムスタンプ付きのレポートファイル名を作成
    output_path = f"outputs/{timestamp_str}_insight_report.md"

    # 生成したMarkdownレポートをoutputsフォルダ配下に保存
    save_markdown_report(report_text, output_path)

    # レポートファイル出力完了をコンソールに表示
    print()
    print(f"Markdown report generated: {output_path}")


if __name__ == "__main__":
    main()
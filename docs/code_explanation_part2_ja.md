##1. このコード解説ログ Part2 の目的

このログは、Insight-Linker MVP の Day5 終了時点で新たに追加・更新された主要ソースファイルについて、
「そのコードが何をしているのか」を後から自分で理解し直せるようにするために作成したものである。
「何をしているか」だけでなく、「なぜその処理が必要なのか」「なぜこの設計にしたのか」まで残すことを意図している。

このドキュメントは、Insight-Linker MVP の開発過程で作成した個人用の学習ログを兼ねた設計メモです。
将来的に英語ドキュメントへ発展させるための下書きという位置付けです。

Part1 では Day3 時点までの入力レイヤー（main.py・models.py・loader.py・3つのJSON）を扱ったが、
Part2 では Day4〜Day5 で追加された「判定ロジック」と「レポート出力」にフォーカスする。

この Part2 では、Day5 時点までに作成・更新された以下のファイルを対象とする。

・app/core_engine.py
・app/report_gen.py
・main.py（Day4〜Day5 での更新分）

Part1 が「入力レイヤー（main/loader/models/JSON）」の説明だったのに対し、
Part2 は「初期トリアージロジックとレポート出力レイヤー」の説明に相当する。

##2. app/core_engine.py の解説

###2-1. ファイル全体の目的

core_engine.py は、Insight-Linker における「初期トリアージロジック」を集約するファイルである。
Day3 までに整備した入力レイヤー（UserActivity・HRContext・AccessPrivilege）を元に、MVP の段階で

・各アクティビティに対して
・3つのルールに基づいてリスクスコアを計算し
・Low / Medium / High のリスクレベルと、理由のリストを返す
という役割を担う。

このファイルがあることで、「入力の読み込み」（loader）と「評価ロジック」（core_engine）を分離でき、
将来ルールを増やしたりスコアリング方法を変えたりする際に、変更箇所をこのファイルに集中させられる。

###2-2. コード本体
from app.models import UserActivity, HRContext, AccessPrivilege


def is_after_hours(timestamp: str) -> bool:
    hour = int(timestamp[11:13])
    return hour < 6 or hour >= 22


def is_allowed_resource(resource_path: str, allowed_resources: list[str]) -> bool:
    return any(resource_path.startswith(prefix) for prefix in allowed_resources)


def evaluate_activity(
    activity: UserActivity,
    hr_contexts: dict[str, HRContext],
    access_privileges: dict[str, AccessPrivilege],
) -> dict:
    user_id = activity.user_id
    hr = hr_contexts.get(user_id)
    privilege = access_privileges.get(user_id)

    risk_score = 0
    reasons = []

    if hr and hr.is_on_leave:
        risk_score += 2
        reasons.append("Access during leave")

    if hr and hr.resignation_notified and is_after_hours(activity.timestamp):
        risk_score += 3
        reasons.append("After-hours access by resignation-notified user")

    if privilege and not is_allowed_resource(
        activity.resource_path, privilege.allowed_resources
    ):
        risk_score += 3
        reasons.append("Access to unauthorized resource")

    if risk_score >= 5:
        risk_level = "High"
    elif risk_score >= 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "user_id": activity.user_id,
        "timestamp": activity.timestamp,
        "action": activity.action,
        "resource_path": activity.resource_path,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "reasons": reasons,
    }

###2-3. 数行ごとの役割と理由
・何をしているか
app/models.py で定義した3つの dataclass を、このファイルで使えるように import している。

・なぜ必要か
型ヒントにより、「どの関数がどのデータ型を扱うのか」が明示され、エディタ補完や静的チェックを活かせる。

・is_after_hours(timestamp: str) -> bool

def is_after_hours(timestamp: str) -> bool:
    hour = int(timestamp[11:13])
    return hour < 6 or hour >= 22
    
・何をしているか
timestamp 文字列から時刻の「時」だけを抜き出し、22時以上または6時未満なら True（時間外）を返す。

・なぜ必要か
「退職通知済み＋深夜アクセス」ルールで使う時間帯判定を関数に切り出すことで、
evaluate_activity の可読性を保ち、将来の時間帯調整も容易にしている。

・is_allowed_resource(resource_path, allowed_resources)

def is_allowed_resource(resource_path: str, allowed_resources: list[str]) -> bool:
    return any(resource_path.startswith(prefix) for prefix in allowed_resources)
    
・何をしているか
アクセスした resource_path が、許可されたプレフィックス群 allowed_resources のいずれかで始まっていれば True を返す。

・なぜ必要か
MVP では、複雑な権限モデルではなく「許可ディレクトリリストとのプレフィックス一致」というシンプルな形にしている。
関数として分離することで、後から判定ロジックを差し替えやすくしている。


・evaluate_activity(...) のヘッダ

def evaluate_activity(
    activity: UserActivity,
    hr_contexts: dict[str, HRContext],
    access_privileges: dict[str, AccessPrivilege],
) -> dict:

・何をしているか
1件の UserActivity と、user_id をキーにした HR / 権限辞書を受け取り、リスク評価結果の dict を返す中核関数である。

・なぜ必要か
main 側から見ると「1イベントごとに evaluate_activity を呼ぶ」だけで済むようになり、判定ロジックの変更をこの関数に集約できる。

・ユーザーごとの HR / 権限情報取得

    user_id = activity.user_id
    hr = hr_contexts.get(user_id)
    privilege = access_privileges.get(user_id)

・何をしているか
現在評価中のイベントの user_id を取り出し、そのユーザーに対応する HR コンテキストと権限情報を辞書から取得している。

・なぜ必要か
行動ログ単体ではリスクを判断しにくいため、「休暇中か」「退職予定か」「どのパスにアクセス可能か」
といった文脈情報と組み合わせて評価する設計にしている。

・スコアと理由の初期化

    risk_score = 0
    reasons = []

・何をしているか
リスクスコアを 0 で開始し、ルールごとに加算していく。reasons は、そのイベントに対してどのルールが働いたかを記録するリストである。

・なぜ必要か
複数ルールの合算で High/Medium/Low を決める構造と、「なぜそうなったか」をレポートに出せるようにするため。


・休暇中アクセスルール

    if hr and hr.is_on_leave:
        risk_score += 2
        reasons.append("Access during leave")

・何をしているか
HR 情報があり、そのユーザーが is_on_leave == True なら、スコア +2 と理由の追加を行う。

・なぜ必要か
Insider Risk の典型的なシグナルである「休暇中のアクセス」を、MVPの段階からルールとして明示的に持たせている。


・退職通知済み＋時間外アクセスルール

    if hr and hr.resignation_notified and is_after_hours(activity.timestamp):
        risk_score += 3
        reasons.append("After-hours access by resignation-notified user")

・何をしているか
HR 情報があり、resignation_notified == True かつ is_after_hours が True の場合、スコア +3 と理由追加を行う。

・なぜ必要か
「退職予定者の深夜アクセス」は実務でもよく挙げられるリスクパターンであり、
時間帯と HR 状態の掛け合わせを表現するためのルールになっている。

・許可外リソースアクセスルール

    if privilege and not is_allowed_resource(
        activity.resource_path, privilege.allowed_resources
    ):
        risk_score += 3
        reasons.append("Access to unauthorized resource")

・何をしているか
権限情報があり、かつ resource_path が許可されたプレフィックスに一致しない場合、スコア +3 と理由を追加する。

・なぜ必要か
「権限外の場所へのアクセス」は、Insider Risk に限らず重大なシグナルであり、MVP の段階でも必ず押さえておきたい要素だからである。

・スコアからリスクレベルを決める

    if risk_score >= 5:
        risk_level = "High"
    elif risk_score >= 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"


・何をしているか
累積された risk_score に応じて、High/Medium/Low の3段階に分類している。

・なぜ必要か
レポートや UI では、生の点数よりラベルの方が直感的であり、閾値をこの部分に集約しておくと調整もしやすい。

・最終的な dict を返す

    return {
        "user_id": activity.user_id,
        "timestamp": activity.timestamp,
        "action": activity.action,
        "resource_path": activity.resource_path,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "reasons": reasons,
    }

・何をしているか
入力の主要フィールドに、計算された risk_level・risk_score・reasons を加えた dict を返している。

・なぜ必要か
後続の main.py や report_gen.py にとって扱いやすい「評価結果フォーマット」を統一するため。
将来 EvaluationResult dataclass を導入する際も、この構造をそのまま写せば移行が容易になる。


##3. app/report_gen.py の解説
###3-1. ファイル全体の目的

・app/report_gen.py は、判定結果を「人間が読むレポート」に変換するための出力レイヤーを担当するファイルである。
・Day5 では、ここに Markdown レポート生成と保存のロジックを実装し、
・High / Medium の詳細な Findings
・Low を含む全体 Summary
・ヘッダ・Notes による文脈情報
を含むレポートを、タイムスタンプ付きファイル名で出力できるようにした。

###3-2. コード本体

from pathlib import Path
from datetime import datetime


def build_markdown_report(results: list[dict]) -> str:
    total_count = len(results)
    high_results = [r for r in results if r["risk_level"] == "High"]
    medium_results = [r for r in results if r["risk_level"] == "Medium"]
    low_results = [r for r in results if r["risk_level"] == "Low"]

    # 対象ユーザー数（ユニーク user_id 数）
    unique_users = len({r["user_id"] for r in results})

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
                f"### User {result['user_id']} / {result['timestamp']}",
                f"- Risk level: {result['risk_level']}",
                f"- Risk score: {result['risk_score']}",
                f"- Reasons: {', '.join(result['reasons']) if result['reasons'] else 'None'}",
                "",
            ])

    if medium_results:
        lines.append("## Medium Risk Findings")
        lines.append("")
        for result in medium_results:
            lines.extend([
                f"### User {result['user_id']} / {result['timestamp']}",
                f"- Risk level: {result['risk_level']}",
                f"- Risk score: {result['risk_score']}",
                f"- Reasons: {', '.join(result['reasons']) if result['reasons'] else 'None'}",
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

###3-3. 数行ごとの役割と理由

・import 行

from pathlib import Path
from datetime import datetime

Path は出力パスの扱いを楽にするため、
datetime はヘッダの「Generated at」にタイムスタンプを埋め込むために使っている。

・build_markdown_report(results: list[dict])

    total_count = len(results)
    high_results = [r for r in results if r["risk_level"] == "High"]
    medium_results = [r for r in results if r["risk_level"] == "Medium"]
    low_results = [r for r in results if r["risk_level"] == "Low"]

評価結果リストから、件数と High / Medium / Low ごとのサブリストを作っている。


    unique_users = len({r["user_id"] for r in results})

ユーザーのユニーク数を数え、「何ユーザー分のイベントか」をヘッダに表示するために使っている。


    if total_count > 0:
        high_pct = round(len(high_results) / total_count * 100)
        medium_pct = round(len(medium_results) / total_count * 100)
        low_pct = round(len(low_results) / total_count * 100)
    else:
        high_pct = medium_pct = low_pct = 0

件数が 0 の場合でもゼロ除算で落ちないようにガードしつつ、High/Medium/Low の割合を出している。

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

レポートのヘッダ＋Summary を組み立てている。
Target period は現状サンプルデータが 2026-05-01 のみであるため固定文言だが、将来は期間算出ロジックに置き換え可能。
Scoring profile で「MVP v1 が3ルールに基づく」ことを一行で示し、ロジックバージョンの説明をしやすくしている。


    if high_results:
        ...
    if medium_results:
        ...

High と Medium のイベントだけ、詳細な Findings セクションを作っている。
Low は Summary にのみ計上し、「ノイズになりやすい Low を詳細から省略する」というトリアージ的な振る舞いを表現している。



    lines.extend([
        "## Notes",
        "",
        "- This report is generated from the current MVP scoring logic.",
        "- Low risk events are counted in the summary but omitted from detailed findings.",
        "- Data in this report is sample data for MVP verification.",
        "- Current rules focus on leave status, resignation notice, and unauthorized resource access.",
        "",
    ])
Notes で、「MVPロジックであること」「Low の扱い」「サンプルデータ」「ルールの範囲」の4点を明示し、
読み手が前提を誤解しないようにしている。



・save_markdown_report(report_text, output_path)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text, encoding="utf-8")

出力パスの親ディレクトリを作成してから、UTF-8 でレポート本文を書き込んでいる。
最初の実行時に outputs ディレクトリがなくてもエラーにならないようにしている点がポイント。


##4. main.py の解説（Day5 時点）
###4-1. ファイル全体の目的（更新版）

Day5 時点の main.py は、Insight-Linker のエントリーポイントとして、

・3種類の入力データを読み込む
・各アクティビティを evaluate_activity で評価し、コンソールに結果を表示する
・すべての結果を results に蓄積し、Markdown レポートを生成・保存する
という一連の流れを制御している。

Day3 までは「セットアップと件数確認」だけだったが、
Day4〜Day5 を経て「入力→判定→レポート出力」まで含むメインルーチンになった。

###4-2. コード本体

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
            f"user_id={result['user_id']}, "
            f"timestamp={result['timestamp']}, "
            f"risk_level={result['risk_level']}, "
            f"risk_score={result['risk_score']}, "
            f"reasons={result['reasons']}"
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


###4-3. 数行ごとの役割と理由

・import ブロック
それぞれに役割コメントを付けることで、「この main.py が何を orchestrate しているか」がひと目で分かるようになっている。

・loader 関数の import
・core_engine の evaluate_activity
・report_gen の build_markdown_report と save_markdown_report
・レポートファイル名用の datetime

Part1 と同じく、「何のための import か」をコメントに残すことで、後から解説ログや README に転用しやすい形になっている。

・main() の前半：入力読み込みと件数表示
    user_activities = load_user_activities("data/raw/user_activity.json")
    hr_contexts = load_hr_contexts("data/raw/hr_context.json")
    access_privileges = load_access_privileges("data/raw/access_privileges.json")
    
loader.py に分離した読み込みロジックを呼び出し、3種類の入力をそれぞれ専用の変数に保持している。


    print("Insight-Linker MVP setup complete")
    print(f"Loaded user activities: {len(user_activities)}")
    print(f"Loaded HR contexts: {len(hr_contexts)}")
    print(f"Loaded access privileges: {len(access_privileges)}")
    print()

セットアップ完了メッセージと、読み込んだ件数を出力し、入力レイヤーが正常に動作していることを目視確認できるようにしている。

・評価ループと results の蓄積
    print("=== Evaluation Results ===")

    results = []

    for activity in user_activities:
        result = evaluate_activity(activity, hr_contexts, access_privileges)
        results.append(result)
        print(
            f"user_id={result['user_id']}, "
            f"timestamp={result['timestamp']}, "
            f"risk_level={result['risk_level']}, "
            f"risk_score={result['risk_score']}, "
            f"reasons={result['reasons']}"
        )

evaluate_activity を全アクティビティに対して適用し、
コンソールには読みやすい形で出力
同時に results リストに結果 dict を蓄積している。

「表示」と「レポート生成」の両方で同じ結果を使うことで、二重計算を避け、整合性も確保している。

・レポート生成と保存

    report_text = build_markdown_report(results)
    
 蓄積した結果から Markdown 文字列を生成する。出力の構造は report_gen.py に委譲している。
 
 
     timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/{timestamp_str}_insight_report.md"
 
 実行時刻を元に YYYYMMDD_HHMMSS 形式の文字列を作成し、それを含んだファイル名を組み立てる。
これにより、実行するたびに異なるファイル名となり、レポートが上書きされずに履歴として残る。

    save_markdown_report(report_text, output_path)
    print()
    print(f"Markdown report generated: {output_path}")
 
 
report_gen.py に委譲してレポートを保存し、そのパスをコンソールに表示して完了を知らせる。

・エントリーポイント

if __name__ == "__main__":
    main()

main.py が直接実行されたときだけ main() を呼び出す、Python の標準的なエントリーポイント構文。
これにより、他モジュールから main を import しても勝手に実行されないようにしている。


##5. Part2 全体の位置づけ

この Part2 では、Day4〜Day5 で追加・更新された

・app/core_engine.py（初期トリアージロジック）
・app/report_gen.py（Markdown レポート生成・保存）
・main.py（入力→評価→レポート出力の制御）
について、実際のコード全文と、その意図・役割・理由を整理した。

Part1（入力レイヤー）と合わせることで、Insight-Linker MVP の
・入力/判定/出力
という一周を、コードレベルで再現・説明できる状態になった。


# Insight-Linker（日本語概要）

Insight-Linker は、インサイダーリスクの初期トリアージを想定した軽量な Python CLI ツールです。  
ユーザー行動ログ、HR コンテキスト、アクセス権限情報を組み合わせて、注意が必要なイベントを抽出し、説明可能な Markdown レポートを生成します。

このプロジェクトは、小さな MVP として、インフラ運用寄りの生データを、ガバナンスやセキュリティの文脈とどう結びつけられるかを検証する目的で作成しました。

> Main documentation is maintained in English in the repository root `README.md`.  
> この日本語版は補助的な概要資料であり、今後の更新は最小限を想定しています。

---

## このプロジェクトの意図

インサイダーリスクは、単一のログだけでは見えにくいことが多いです。  
たとえば 1 件のファイルアクセスも、休職中・退職通知後・本来の許可範囲外アクセスといった周辺情報を重ねると、意味が大きく変わります。

Insight-Linker は、その考え方をコードとして小さく実装したものです。  
複数のコンテキストを突き合わせ、単純なルールベースでリスクスコアを付け、なぜフラグされたのかを理由付きで出力します。

---

## 主な機能

- ユーザー行動、HR 情報、アクセス権限のサンプルデータ読み込み
- ルールベースのイベント単位リスク評価
- `Low / Medium / High` のリスク分類
- `EvaluationResult` dataclass による構造化結果の返却
- 判定理由の人間可読な出力
- Medium / High イベントを中心とした Markdown レポート生成
- Day7 サンプルログのセッション単位分析
- セッション結果をもとにしたユーザー単位リスク集約
- セッション単位・ユーザー単位の表を含むレポート生成

---

## 想定ユースケース

たとえば、あるユーザーのファイルアクセスイベントが次の条件と重なった場合を考えます。

- 休職中である
- 退職通知後の時間外アクセスである
- 許可されていないリソース範囲に対するアクセスである

Insight-Linker は、そのイベントにスコアを付けるだけでなく、どの条件によりリスク判定されたのかを理由として残します。  
さらに Day7 拡張では、単発イベントだけでなく、一定時間内の連続行動を 1 セッションとしてまとめ、行動パターンとして評価します。

---

## Project structure

```text
.
├─ app/
│  ├─ core_engine.py      # Risk scoring logic
│  ├─ loader.py           # JSON -> dataclass loaders
│  ├─ models.py           # Domain models and EvaluationResult
│  └─ report_gen.py       # Markdown report generator
│
├─ data/
│  ├─ access_privileges.json
│  ├─ hr_context.json
│  ├─ user_activity.json
│  └─ day7_sample_logs.csv
│
├─ outputs/
│  └─ (generated) insight reports
│
├─ requirements.txt
├─ day7_analysis.py       # Session and user-level risk aggregation
├─ main.py
└─ README.md
```

---

## 現在のスコアリング概要

イベント単位では、現在の MVP として次の 3 ルールを実装しています。

- 休職中アクセス
- 退職通知済みユーザーによる時間外アクセス
- 許可されていないリソースへのアクセス

これらは意図的に小さく明示的なルールとして実装しており、読みやすさ・説明しやすさ・拡張しやすさを優先しています。

---

## Day7 セッション分析

イベント単位評価に加え、Day7 ではログをセッション単位でまとめて評価する処理を追加しています。

### セッション分割

- `user_id` ごとに時系列でイベントを並べる
- 連続イベントの間隔が **30 分以上** 空いたら新しいセッションとみなす

### セッション評価ルール

現時点では、以下のような条件を使ってセッションスコアを算出しています。

- 深夜帯の活動（`22:00-05:59 JST`）
- `/restricted/` リソースへのアクセス
- restricted リソースのダウンロード
- 権限変更操作
- denied イベントの発生
- 同一セッション内での複数 denied

### ユーザー単位集約

各ユーザーの最終リスクは、そのユーザーに観測されたセッションのうち、最も高いリスクレベルを基準に集約します。  
あわせて、合計スコア、セッション数、High / Medium / Low セッション数も出力します。

---

## 技術スタック

- Python 3.13.13
- `dataclasses`
- JSON サンプル入力
- CSV サンプル入力（Day7 用）
- ルールベースのスコアリング
- Markdown レポート生成
- `pandas` による Day7 集計処理

---

## 実行方法

### 1. Clone

```bash
git clone https://github.com/tomohitotoyomura-hub/insight-linker.git
cd insight-linker
```

### 2. 仮想環境作成（任意）

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 4. 実行

```bash
python main.py
```

---

## 実行時に行うこと

`python main.py` を実行すると、以下を行います。

1. `data/` 配下のサンプルデータを読み込む
2. イベント単位でリスク評価する
3. 結果をコンソールに表示する
4. Day7 セッション分析を実行する
5. セッション単位・ユーザー単位の結果を表示する
6. `outputs/` 配下に Markdown レポートを生成する

---

## 補足ドキュメント

日本語の補助資料として、以下を `docs/` 配下に配置しています。

- `code_explanation_part1_ja.md`
- `code_explanation_part2_ja.md`
- `code_explanation_part3_ja.md`

これらは、Day3〜Day8 にかけての設計・実装意図を日本語で整理した補足メモです。  
英語版 README がリポジトリの主文書であり、詳細の最新状態はそちらを基準としてください。

---

## 今後の改善候補

- イベント単位 findings のユーザー単位グルーピング
- HR / 権限情報欠損時の扱い改善
- レポート体裁の改善
- テスト追加
- 入力バリデーション強化
- 対応する insider risk シナリオの追加

---

## 注意

- このリポジトリ内のデータは、MVP 検証用のサンプルデータです。
- 本プロジェクトは学習・ポートフォリオ用途であり、本番運用向けの検知基盤ではありません。
- イベント単位分析と Day7 セッション分析は、意図的に別サンプルデータを用いています。
- 最新かつ正式な説明は英語版 `README.md` を参照してください。

---

## License

MIT
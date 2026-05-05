##1. このコード解説ログの目的
このログは、Insight-Linker MVP の Day3 終了時点で存在している主要ソースファイルとデータファイルについて、
「そのコードやデータが何をしているのか」を後から自分で理解し直せるようにするために作成したものである。
「何をしているか」だけでなく、「なぜその処理が必要なのか」「なぜこの設計にしたのか」まで残すことを意図している。

このドキュメントは、Insight-Linker MVP の開発過程で作成した個人用の学習ログを兼ねた設計メモです。
将来的に英語ドキュメントへ発展させるための下書きという位置付けです。

この Part1 では、Day3 時点までに作成された以下のファイルを対象とする。

・main.py
・app/models.py
・app/loader.py
・data/raw/user_activity.json
・data/raw/hr_context.json
・data/raw/access_privileges.json


##2. main.py の解説
###2-1. ファイル全体の目的
main.py は、この Insight-Linker プロジェクトのエントリーポイントとして機能するファイルである。
現在の MVP 段階では、ここで

・loader を呼び出し
・3種類の入力データを読み込み
・正しく読めた件数をコンソールに表示する

という最小限の動作確認を行っている。
このファイルが必要なのは、プロジェクト全体に「どこから実行を開始するか」を明示するためである。
もし main.py が無ければ、各モジュールを個別に動かすしかなくなり、MVP 全体の流れを一度に確認しづらくなる。

###2-2. コード本体

from app.loader import (
    load_user_activities,
    load_hr_contexts,
    load_access_privileges,
)


def main() -> None:
    user_activities = load_user_activities("data/raw/user_activity.json")
    hr_contexts = load_hr_contexts("data/raw/hr_context.json")
    access_privileges = load_access_privileges("data/raw/access_privileges.json")

    print("Insight-Linker MVP setup complete")
    print(f"Loaded user activities: {len(user_activities)}")
    print(f"Loaded HR contexts: {len(hr_contexts)}")
    print(f"Loaded access privileges: {len(access_privileges)}")


if __name__ == "__main__":
    main()
    

2-3. 数行ごとの役割と理由
「import ブロック」
from app.loader import (
    load_user_activities,
    load_hr_contexts,
    load_access_privileges,
)

何をしているか
・app/loader.py に定義した3つの読み込み関数を、このファイルで使えるように import している。

何のためのブロックか
・データの読み込み処理を main.py の中に直接書かず、別モジュールに分離したうえで、それを呼び出すための入り口を作っている。

なぜ必要か
・読み込みロジックを main.py に直書きすると、実行制御とデータ処理が混ざって見通しが悪くなる。
・loader.py に役割を分けることで、「main は流れを制御する」「loader は入力を読む」という責務分離ができる。
・今後、読み込み処理を修正しても main.py 側の変更を小さくできる。

「def main() -> None:」
def main() -> None:

何をしているか
・メイン処理を main() 関数として定義している。

何のためのブロックか
・実行時の本体処理を関数にまとめている。

なぜ必要か
・処理を関数にまとめないと、ファイルを import しただけでコードが上から実行されてしまう。
・今後テストや機能追加をするときにも、メインの流れが関数としてまとまっていた方が扱いやすい。

「JSON 読み込み部分」
user_activities = load_user_activities("data/raw/user_activity.json")
hr_contexts = load_hr_contexts("data/raw/hr_context.json")
access_privileges = load_access_privileges("data/raw/access_privileges.json")

何をしているか
・3つの JSON ファイルをそれぞれ対応する関数で読み込み、その結果を変数に格納している。

何のためのブロックか
・Insight-Linker が扱う3種類の入力データを、実行開始時にメモリ上へ取り込むため。

なぜ必要か
・このプロジェクトは「ユーザー行動」「HRコンテキスト」「権限情報」の3軸を相関させる設計なので、まずそれらを同時に読み込めなければ次の判定ロジックへ進めない。
・読み込みを別々の変数に保持することで、後続の core_engine.py でそれぞれの役割を明確に使い分けられる。

「print() ブロック」
print("Insight-Linker MVP setup complete")
print(f"Loaded user activities: {len(user_activities)}")
print(f"Loaded HR contexts: {len(hr_contexts)}")
print(f"Loaded access privileges: {len(access_privileges)}")

何をしているか
・セットアップ完了メッセージと、読み込んだ各データ件数をコンソールに表示している。

何のためのブロックか
・Day3時点で、loader が正しく動作していることを目視で確認するため。

なぜ必要か
・読み込み処理は成功しても、件数がずれていれば JSON や dataclass の整合性に問題がある可能性がある。
・単に「エラーが出ない」だけでなく、「期待した件数が読めている」ことを確認することで、入力レイヤーの妥当性を確かめられる。

「if __name__ == "__main__":」
if __name__ == "__main__":
    main()
    
何をしているか
・このファイルが直接実行されたときだけ main() を呼び出す。

何のためのブロックか
・main.py をエントリーポイントとして安全に実行可能にするため。

なぜ必要か
・この書き方が無いと、将来ほかのモジュールから main.py を import しただけで処理が勝手に走ってしまう可能性がある。
・ython の標準的な実行パターンに従うことで、後から見たときにも意図が分かりやすい。


##3. app/models.py の解説
###3-1. ファイル全体の目的
models.py は、Insight-Linker が扱う入力データの構造を Python の dataclass として明示するためのファイルである。
このファイルが必要なのは、JSON から読み込んだデータを単なる辞書のまま扱うのではなく、
「どのような属性を持つデータなのか」をコード上で固定し、設計のぶれを防ぐためである。

###3-2. コード本体
from dataclasses import dataclass
from typing import List


@dataclass
class UserActivity:
    """
    SIEM やログ管理システムから取得したユーザーアクティビティの1イベント分。
    MVP では timestamp は文字列、resource_path は単純なパス文字列として扱う。
    """
    timestamp: str
    user_id: str
    action: str
    resource_path: str


@dataclass
class HRContext:
    """
    人事システムのコンテキスト情報。
    休暇中かどうか、退職通知済みかどうか、所属部署などを表す。
    """
    user_id: str
    is_on_leave: bool
    resignation_notified: bool
    department: str


@dataclass
class AccessPrivilege:
    """
    権限管理（AD 等）の情報。
    ユーザーの権限レベルと、アクセスを許可されたリソースの一覧。
    """
    user_id: str
    privilege_level: str
    allowed_resources: List[str]
    
###3-3. 数行ごとの役割と理由
「import 部分」
from dataclasses import dataclass
from typing import List

何をしているか
・@dataclass を使うための dataclass と、型ヒント用の List を import している。

何のためのブロックか
・モデルクラスを簡潔に定義しつつ、各属性の型を明示するための準備。

なぜ必要か
・dataclass を使うことで、__init__ などを自分で書かずに済み、データ構造の宣言に集中できる。
・型ヒントを付けることで、VS Code や後続の自分が「この属性には何が入るべきか」を理解しやすくなる。

「UserActivity」
@dataclass
class UserActivity:

何をしているか
・ユーザー行動ログ1件分を表すデータモデルを定義している。

何のためのブロックか
・SIEM やアクセスログ由来のイベントを、一定の形で保持するため。

なぜ必要か
・Insight-Linker は「イベント単位」でリスクを見る設計なので、まず1イベントをどう表現するかを決める必要がある。
・ここが曖昧だと、後でタイムスタンプや resource_path の扱いが人によってぶれる。

timestamp: str
user_id: str
action: str
resource_path: str

「timestamp: str」
・イベント発生時刻。MVPではまず文字列として扱い、時刻処理の複雑化を避ける。

「user_id: str」
・他データと突合するためのキー。Insight-Linker では相関の中心になる。

「action: str」
・どの種類の行動かを示す。将来的に file_access 以外にも拡張可能。

「resource_path: str」
・何にアクセスしたかを示すパス。権限外アクセス判定に使う前提。

「HRContext」
@dataclass
class HRContext:

何をしているか
・人事コンテキストを表すデータモデルを定義している。

何のためのブロックか
・技術ログだけでは判断できない「休暇中」「退職通知済み」などの文脈を加えるため。

なぜ必要か
・Insider Risk 的な評価では、同じアクセスでも「通常勤務中」か「退職前」かで意味が変わる。
・その差分を扱うため、HR文脈を独立したモデルにしている。

user_id: str
is_on_leave: bool
resignation_notified: bool
department: str

「user_id: str」
・行動ログと突合するためのキー

「is_on_leave: bool」
・休暇中アクセス検知の基礎になる

「resignation_notified: bool」
・退職通知済みユーザーの挙動を見る基礎になる

「department: str」
・将来的なレポートや分析で部署情報を出すための最小属性

「AccessPrivilege」
@dataclass
class AccessPrivilege:

何をしているか
・権限情報を表すデータモデルを定義している。

何のためのブロックか
・ユーザーが本来アクセスできる範囲を保持するため。

なぜ必要か
・単にアクセスログを見るだけでは、そのアクセスが妥当かどうか判断できない。
・「許可された範囲」と比較して初めて、権限外アクセスの候補を洗い出せる。

user_id: str
privilege_level: str
allowed_resources: List[str]

「user_id: str」
・ログや HR 情報と結びつけるキー。

「privilege_level: str」
・ユーザーの権限の強さをざっくり表現する。

「allowed_resources: List[str]」
・許可された共有パスの一覧。複数の領域を持てるようにするため配列にしている。

##4. app/loader.py の解説
###4-1. ファイル全体の目的
loader.py は、JSON ファイルを読み込み、models.py で定義した dataclass に変換して返すためのモジュールである。
このファイルが必要なのは、ファイル読み込みという共通処理を main.py や今後の core_engine.py から分離し、入力処理の責務を一箇所にまとめるためである。

###4-2. コード本体

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
 
 
 ###4-3. 数行ごとの役割と理由
 「import ブロック」
 import json
from pathlib import Path

from app.models import UserActivity, HRContext, AccessPrivilege

何をしているか
・JSON 読み込み、ファイルパス操作、dataclass 変換に必要なモジュールを取り込んでいる。

何のためのブロックか
・loader モジュールの役割を実現するための基本部品を揃えている。

なぜ必要か
・json が無ければ JSON ファイルを Python データへ変換できない。
・Path が無ければファイルパスをやや生の文字列頼りで扱うことになり、見通しが悪くなる。
・dataclass の import が無ければ、辞書を構造化されたデータとして返せない。

「load_user_activities」
def load_user_activities(file_path: str) -> list[UserActivity]:

何をしているか
・ユーザー行動ログJSONを読み込んで、UserActivity のリストとして返す関数を定義している。

何のためのブロックか
・イベント群を時系列順に近い形で保持し、後続で順番に評価できるようにするため。

なぜ必要か
・ログは通常「イベントの集合」なので、辞書ではなくリストのまま持つ方が自然で、for ループ処理に向いている。

path = Path(file_path)

・文字列のファイルパスを Path オブジェクトに変換している。
・これにより、ファイル操作を path.open() のような形で書ける。
・パスの扱いを明確にし、可読性を上げるために必要。

with path.open("r", encoding="utf-8") as f:
    raw_data = json.load(f)

・ファイルを読み取りモードで開き、UTF-8 で読み込み、JSON を Python のリスト／辞書へ変換している。
・with を使うことで、処理後にファイルを自動的に閉じる。
・ファイルハンドルの閉じ忘れを防ぎ、安全に読み込むために必要。

activities = [UserActivity(**item) for item in raw_data]
return activities

・JSON の各辞書レコードを UserActivity のインスタンスに変換し、その一覧を返している。
・**item は辞書のキーを引数名として展開する記法。
・この変換が必要なのは、以後の処理で「辞書のキー名を毎回文字列で指定する」より、「属性として扱う」方が安全で読みやすいからである。

def load_hr_contexts(file_path: str) -> dict[str, HRContext]:

何をしているか
・HRコンテキスト JSON を読み込み、user_id をキーとした辞書に変換して返す関数を定義している。

何のためのブロックか
・行動ログ1件ごとに、該当ユーザーの HR 情報を即座に引けるようにするため。

なぜ必要か
・リストのままだと、毎回 user_id を総当たりで探す必要がある。
・dict[str, HRContext] にしておけば、hr_contexts[user_id] で素早くアクセスできる。

hr_contexts = {item["user_id"]: HRContext(**item) for item in raw_data}
return hr_contexts

・JSON の各レコードを HRContext に変換し、その user_id をキーとして辞書化している。
・これにより、ログイベントごとの相関処理が簡単になる。
・Insight-Linker の中心は相関分析なので、この辞書化は非常に重要な前処理である。

「load_access_privileges」
def load_access_privileges(file_path: str) -> dict[str, AccessPrivilege]:

何をしているか
・権限情報JSONを読み込み、user_id をキーとした辞書として返す関数を定義している。

何のためのブロックか
・各イベントに対して、そのユーザーが本来アクセス可能な領域をすぐに参照できるようにするため。

なぜ必要か
・権限外アクセス判定をするには、「イベント」だけでなく「その人の許可範囲」を高速に引ける必要がある。
・そのため HR 情報と同様、辞書構造で持つのが合理的である。

access_privileges = {
    item["user_id"]: AccessPrivilege(**item) for item in raw_data
}
return access_privileges

・各権限レコードを dataclass に変換し、user_id ごとに辞書へ格納している。
・これにより、Day4以降のルール実装で access_privileges[activity.user_id] のように直感的に使える。

##5. data/raw/user_activity.json の解説
###5-1. ファイル全体の目的
この JSON ファイルは、ユーザー行動ログのダミーデータを保持するためのものである。
MVP 段階では、本物の SIEM や EDR からデータを取得するのではなく、まずは開発用の小さなサンプルを用いてロジックを組み立てることを目的としている。
このファイルが必要なのは、loader.py や将来の core_engine.py が「何を入力として受け取るか」を具体化するためである。

###5-2. データ本体

[
  {
    "timestamp": "2026-05-01T22:30:00",
    "user_id": "u001",
    "action": "file_access",
    "resource_path": "\\\\fileserver01\\finance\\q2_forecast.xlsx"
  },
  {
    "timestamp": "2026-05-01T02:15:00",
    "user_id": "u002",
    "action": "file_access",
    "resource_path": "\\\\fileserver01\\hr\\salary_master.xlsx"
  },
  {
    "timestamp": "2026-05-01T10:05:00",
    "user_id": "u003",
    "action": "file_access",
    "resource_path": "\\\\fileserver01\\it\\runbook.pdf"
  },
  {
    "timestamp": "2026-05-01T23:45:00",
    "user_id": "u001",
    "action": "file_access",
    "resource_path": "\\\\fileserver01\\finance\\budget_raw.csv"
  }
]

###5-3. ブロックとしての役割と理由
外側の [ ]
・複数イベントを配列として保持する。
・ログは通常1件ではなく複数件の集合なので、配列構造が自然。

各オブジェクト
・1件のログイベントを表している。
・この単位を UserActivity に変換する前提で作っている。

timestamp
・発生時刻。将来、深夜アクセス判定などに使う。

user_id
・HR / 権限情報とつなぐためのキー。

action
・行動の種別。今は file_access だけだが将来拡張可能。

resource_path
・アクセス対象。権限外アクセス検知に使う。

###5-4. なぜこのサンプル構成にしたか
u001 に夜間アクセスを2件入れている
・退職通知済みユーザーの深夜アクセスというシナリオを表現するため。

u002 に深夜帯相当のアクセスを置いている
・休暇中アクセスや HR 文脈と組み合わせる候補にするため。

u003 は比較的通常業務らしいイベントとして置いている
・正常系に近いデータも入れて、比較対象を持たせるため。

##6. data/raw/hr_context.json の解説
###6-1. ファイル全体の目的
このファイルは、人事コンテキストのダミーデータを保持するためのものである。
Insight-Linker が Insider Risk 的なニュアンスを持つためには、技術ログだけでなく「そのユーザーがどのような状態にあるか」という HR 文脈が必要になる。

###6-2. データ本体
[
  {
    "user_id": "u001",
    "is_on_leave": false,
    "resignation_notified": true,
    "department": "Finance"
  },
  {
    "user_id": "u002",
    "is_on_leave": true,
    "resignation_notified": false,
    "department": "HR"
  },
  {
    "user_id": "u003",
    "is_on_leave": false,
    "resignation_notified": false,
    "department": "IT Operations"
  }
]

###6-3. ブロックとしての役割と理由
user_id
・行動ログとの突合キー。

is_on_leave
・休暇中アクセスを検知するための属性。

resignation_notified
・退職通知済みユーザーの振る舞いを見るための属性。

department
・レポートや説明に文脈を持たせるための部署情報。

###6-4. なぜこのサンプル構成にしたか
u001 を resignation_notified: true にした
・深夜アクセスと組み合わせて、典型的なリスクルールを後で試せるようにするため。

u002 を is_on_leave: true にした
・「休暇中なのにアクセスがある」というルール検証のため。

u003 を通常状態にした
・比較対象となるベースラインを持たせるため。

##7. data/raw/access_privileges.json の解説
###7-1. ファイル全体の目的
このファイルは、各ユーザーの権限情報のダミーデータを保持するためのものである。
Insight-Linker では、「アクセスがあった」という事実だけでなく、「そのアクセスが許可範囲内かどうか」も判定対象にしたいため、このファイルが必要である。

###7-2. データ本体

[
  {
    "user_id": "u001",
    "privilege_level": "high",
    "allowed_resources": [
      "\\\\fileserver01\\finance\\",
      "\\\\fileserver01\\shared\\"
    ]
  },
  {
    "user_id": "u002",
    "privilege_level": "medium",
    "allowed_resources": [
      "\\\\fileserver01\\hr\\",
      "\\\\fileserver01\\shared\\"
    ]
  },
  {
    "user_id": "u003",
    "privilege_level": "low",
    "allowed_resources": [
      "\\\\fileserver01\\it\\",
      "\\\\fileserver01\\shared\\"
    ]
  }
]

7-3. ブロックとしての役割と理由
user_id
・ログおよび HR 情報との結合キー。

privilege_level
・権限の強さをざっくり表現する属性。将来スコアリングに使える余地がある。

allowed_resources
・許可されたリソースの一覧。複数領域を表現できるよう配列にしている。

###7-4. なぜこのサンプル構成にしたか
・各ユーザーに、自部署相当のフォルダと shared を許可している
・シンプルながら、「許可された範囲」と「外れたアクセス」を比較しやすくするため。
・privilege_level に high / medium / low を置いている
将来的にスコアリングへ拡張しやすいよう、今のうちから属性を持たせておくため。

##8. Day3時点での全体設計上の意味
Day3時点のコード群は、見た目にはまだ小さいが、役割分担はかなり明確である。

main.py
・実行の入口

models.py
・データ構造の定義

loader.py
・入力データの読み込みと変換

data/raw/*.json
・開発用のサンプル入力

この分離が重要なのは、今後 core_engine.py を追加したときに、
・入力
・モデル
・判定
・出力

を別々に考えられるようになるからである。
もし Day3 の時点でこれらを1ファイルに詰め込んでいたら、後の修正やブログ用の説明がかなり難しくなっていたはずである。

##9. 次回のコード解説ログで扱うもの
次のコード解説ログ Part2 では、Day4 以降で追加予定の以下を対象にするのが自然である。

・app/core_engine.py
・ルール判定ロジック
・risk_level / reason の設計
・将来追加する report_gen.py

この Part1 は、Insight-Linker における「入力層」と「最小実行構成」の解説として位置づける。



import pandas as pd

# ===== 設定値 =====
SESSION_GAP_SECONDS = 30 * 60  # 30分
NIGHT_START = 22
NIGHT_END = 5  # 0〜5時台を深夜とみなす


# ===== ログ読み込み・前処理 =====
def load_logs(csv_path: str) -> pd.DataFrame:
    """Day7用ログを読み込んで前処理する"""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    return df


# ===== セッションID付与 =====
def assign_session_ids(df: pd.DataFrame) -> pd.DataFrame:
    """user_id ごとに 30 分以上の無操作で session_id を切り替える"""

    # ユーザーごとに timestamp 差分を計算
    time_diff = df.groupby("user_id")["timestamp"].diff().dt.total_seconds()

    # 最初の行、または30分以上空いたら新セッション
    new_session_flag = time_diff.isna() | (time_diff >= SESSION_GAP_SECONDS)

    # user_id ごとに累積和を取り、0始まりの session_id を付与
    df["session_id"] = (
        new_session_flag.groupby(df["user_id"]).cumsum() - 1
    ).astype(int)

    df = df.sort_values(["user_id", "session_id", "timestamp"]).reset_index(drop=True)
    return df


# ===== セッションスコアリング =====
def is_night(ts: pd.Timestamp) -> bool:
    """深夜時間帯(22:00〜05:59)かを判定"""
    hour = ts.tz_convert("Asia/Tokyo").hour if ts.tzinfo is not None else ts.hour
    return (hour >= NIGHT_START) or (hour <= NIGHT_END)


def score_session(session_df: pd.DataFrame) -> dict:
    """1セッション分の DataFrame からスコアを計算"""
    user_id = session_df["user_id"].iloc[0]
    session_id = session_df["session_id"].iloc[0]
    start_time = session_df["timestamp"].min()
    end_time = session_df["timestamp"].max()
    duration = (end_time - start_time).total_seconds()

    has_night = session_df["timestamp"].apply(is_night).any()
    has_restricted = session_df["resource"].astype(str).str.contains("/restricted/", na=False).any()

    actions = session_df["action"].astype(str)
    resources = session_df["resource"].astype(str)

    has_download_restricted = (
        ((actions == "download") & resources.str.contains("/restricted/", na=False))
    ).any()

    has_change_permission = (actions == "change_permission").any()

    results = session_df["result"].astype(str)
    n_denied = (results == "denied").sum()

    score = 0
    reasons = []

    if has_night:
        score += 2
        reasons.append("night_time(+2)")

    if has_restricted:
        score += 2
        reasons.append("restricted_resource(+2)")

    if has_download_restricted:
        score += 3
        reasons.append("restricted_download(+3)")

    if has_change_permission:
        score += 3
        reasons.append("change_permission(+3)")

    if n_denied >= 1:
        score += 1
        reasons.append("denied_once(+1)")

    if n_denied >= 2:
        score += 2
        reasons.append("denied_multiple(+2)")

    if score >= 6:
        risk_level = "High"
    elif score >= 3:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "user_id": user_id,
        "session_id": session_id,
        "session_start": start_time,
        "session_end": end_time,
        "duration_seconds": duration,
        "event_count": len(session_df),
        "score": score,
        "risk_level": risk_level,
        "reasons": ", ".join(reasons),
    }


def build_session_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    """全セッションについてセッション単位のリスクテーブルを返す"""
    rows = []
    for (_, _), group in df.groupby(["user_id", "session_id"]):
        rows.append(score_session(group))

    session_risk_df = pd.DataFrame(rows)

    risk_rank = {"High": 2, "Medium": 1, "Low": 0}
    session_risk_df["risk_rank"] = session_risk_df["risk_level"].map(risk_rank)

    session_risk_df = session_risk_df.sort_values(
        ["risk_rank", "score", "user_id", "session_id"],
        ascending=[False, False, True, True],
    ).drop(columns=["risk_rank"]).reset_index(drop=True)

    return session_risk_df


# ===== ユーザー単位リスク集計 =====
def build_user_risk_table(session_risk_df: pd.DataFrame) -> pd.DataFrame:
    """各ユーザーについて最も高いリスクレベルを最終リスクとする"""
    risk_order = {"Low": 0, "Medium": 1, "High": 2}
    inv_map = {v: k for k, v in risk_order.items()}

    def _agg(group: pd.DataFrame) -> pd.Series:
        max_level_num = group["risk_level"].map(risk_order).max()
        final_level = inv_map[max_level_num]

        return pd.Series({
            "final_risk_level": final_level,
            "total_score": group["score"].sum(),
            "session_count": len(group),
            "high_session_count": (group["risk_level"] == "High").sum(),
            "medium_session_count": (group["risk_level"] == "Medium").sum(),
            "low_session_count": (group["risk_level"] == "Low").sum(),
        })

    user_risk_df = session_risk_df.groupby("user_id").apply(_agg).reset_index()

    user_risk_df["risk_rank"] = user_risk_df["final_risk_level"].map(risk_order)
    user_risk_df = user_risk_df.sort_values(
        ["risk_rank", "total_score"],
        ascending=[False, False],
    ).drop(columns=["risk_rank"]).reset_index(drop=True)

    return user_risk_df


# ===== メイン処理 =====
def run_day7_analysis(csv_path: str = "data/day7_sample_logs.csv"):
    df = load_logs(csv_path)
    df = assign_session_ids(df)

    session_risk_df = build_session_risk_table(df)
    user_risk_df = build_user_risk_table(session_risk_df)

    # ここでは print せず、呼び出し側(main.py)に任せる設計も検討余地あり
    print("=== Session-level risk ===")
    print(session_risk_df.to_string(index=False))

    print("\n=== User-level risk ===")
    print(user_risk_df.to_string(index=False))

    return df, session_risk_df, user_risk_df


if __name__ == "__main__":
    run_day7_analysis()
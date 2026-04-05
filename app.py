from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pandas.tseries.offsets import MonthEnd


DEFAULT_XLSX = "cost_managemant.xlsx"
DEFAULT_SHEET = "cost_sheet"
DATA_CACHE_TTL_SECONDS = 300
FIXED_ITEMS = [
    ("服", "ゆっこ"),
    ("服", "りょう"),
    ("服", "子供"),
    ("化粧品", "-"),
    ("生活費", "外食"),
]


def apply_mobile_friendly_style() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1.5rem;
                max-width: 980px;
            }
            @media (max-width: 768px) {
                .block-container {
                    padding-left: 0.8rem;
                    padding-right: 0.8rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_cost_data(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.shape[1] < 7:
        raise ValueError("cost_sheet の A-H 列が不足しています。")

    cols = list(raw.columns)
    rename_map = {
        cols[0]: "date",
        cols[1]: "kbn1",
        cols[2]: "kbn2",
        cols[3]: "budget_actual",
        cols[6]: "amount",
    }
    df = raw.rename(columns=rename_map)
    required = ["date", "kbn1", "kbn2", "budget_actual", "amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"必要列が見つかりません: {missing}")

    df = df[required].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["kbn1"] = df["kbn1"].astype(str).str.strip()
    df["kbn2"] = df["kbn2"].astype(str).str.strip()
    df["budget_actual"] = (
        df["budget_actual"].astype(str).str.strip().str.replace(" ", "", regex=False)
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df = df.dropna(subset=["date", "amount"])
    df = df[df["budget_actual"].isin(["予算", "実績"])].copy()
    df["month_start"] = df["date"].dt.to_period("M").dt.to_timestamp()

    return df


@st.cache_data(show_spinner=False, ttl=DATA_CACHE_TTL_SECONDS)
def load_cost_data_from_local(file_path: str) -> pd.DataFrame:
    raw = pd.read_excel(file_path, sheet_name=DEFAULT_SHEET, usecols="A:H")
    return normalize_cost_data(raw)


@st.cache_data(show_spinner=False, ttl=DATA_CACHE_TTL_SECONDS)
def load_cost_data_from_upload(uploaded_bytes: bytes) -> pd.DataFrame:
    raw = pd.read_excel(io.BytesIO(uploaded_bytes), sheet_name=DEFAULT_SHEET, usecols="A:H")
    return normalize_cost_data(raw)


def get_period_windows(today: pd.Timestamp) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    month_start = today.replace(day=1)
    month_end = month_start + MonthEnd(1)

    quarter = ((today.month - 1) // 3) + 1
    quarter_end_month = quarter * 3
    ytd_q_start = pd.Timestamp(today.year, 1, 1)
    ytd_q_end = pd.Timestamp(today.year, quarter_end_month, 1) + MonthEnd(1)

    return {
        "当月": (month_start, month_end),
        "年初から四半期末": (ytd_q_start, ytd_q_end),
    }


def aggregate_for_fixed_items(df: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    windows = get_period_windows(today)
    rows: list[dict] = []

    for kbn1, kbn2 in FIXED_ITEMS:
        period_name = "当月" if (kbn1, kbn2) == ("生活費", "外食") else "年初から四半期末"
        start, end = windows[period_name]

        target = df[
            (df["kbn1"] == kbn1)
            & (df["kbn2"] == kbn2)
            & (df["date"] >= start)
            & (df["date"] <= end)
        ]
        sums = target.groupby("budget_actual", as_index=True)["amount"].sum()
        budget = float(sums.get("予算", 0.0))
        actual = float(sums.get("実績", 0.0))

        rows.append(
            {
                "区分1": kbn1,
                "区分2": kbn2,
                "項目": f"{kbn1} / {kbn2}",
                "期間": period_name,
                "予算": budget,
                "実績": actual,
                "残額": budget - actual,
                "期間表示": f"{start.strftime('%Y-%m-%d')} 〜 {end.strftime('%Y-%m-%d')}",
            }
        )

    return pd.DataFrame(rows)


def render_item_bar_chart(summary_df: pd.DataFrame) -> None:
    ordered_items = summary_df["項目"].tolist()
    long_df = summary_df.melt(
        id_vars=["項目"],
        value_vars=["実績", "予算"],
        var_name="区分",
        value_name="金額",
    )
    long_df["項目"] = pd.Categorical(long_df["項目"], categories=ordered_items, ordered=True)
    long_df["区分"] = pd.Categorical(long_df["区分"], categories=["実績", "予算"], ordered=True)
    long_df["ラベル"] = long_df["金額"].map(lambda v: f"{v:,.0f}円")

    fig = px.bar(
        long_df,
        y="項目",
        x="金額",
        color="区分",
        orientation="h",
        barmode="group",
        text="ラベル",
        category_orders={"項目": ordered_items, "区分": ["実績", "予算"]},
        color_discrete_map={"予算": "#1d4ed8", "実績": "#0f766e"},
        title=None,
    )
    fig.update_traces(textposition="outside", cliponaxis=False, selector={"type": "bar"})
    fig.update_layout(
        xaxis_title="金額",
        yaxis_title="",
        legend_title_text="",
        margin=dict(l=20, r=40, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(
        page_title="会計管理ダッシュボード",
        page_icon=":bar_chart:",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    apply_mobile_friendly_style()

    control_left, control_right = st.columns([2, 1])
    with control_left:
        uploaded_file = st.file_uploader(
            "データファイルをアップロード (xlsx)",
            type=["xlsx"],
            help="Cloud ではアップロードを使うと push なしでデータを差し替えられます。",
        )
    with control_right:
        st.write("")
        st.write("")
        if st.button("最新データ読込", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    default_path = Path(__file__).parent / DEFAULT_XLSX
    if uploaded_file is None and not default_path.exists():
        st.error(
            f"データファイルが見つかりません: {default_path}。"
            "ローカルファイルを配置するか、画面からxlsxをアップロードしてください。"
        )
        return

    try:
        if uploaded_file is not None:
            df = load_cost_data_from_upload(uploaded_file.getvalue())
            data_source = f"アップロード: {uploaded_file.name}"
        else:
            df = load_cost_data_from_local(str(default_path))
            data_source = f"ローカル: {default_path.name}"
    except Exception as exc:
        st.error("データを読み込めませんでした。シート名 cost_sheet と A-H 列を確認してください。")
        st.exception(exc)
        return

    if df.empty:
        st.warning("対象データがありません。")
        return

    loaded_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(
        f"データソース: {data_source} | 最終読込: {loaded_at} | "
        f"キャッシュTTL: {DATA_CACHE_TTL_SECONDS // 60}分"
    )

    today = pd.Timestamp.today().normalize()
    summary = aggregate_for_fixed_items(df, today)
    shown = summary.copy()
    shown["対象項目"] = shown["区分1"] + " / " + shown["区分2"]
    shown["期間表示"] = shown["期間表示"]
    shown["予算金額(円)"] = shown["予算"].map(lambda x: f"{x:,.0f} 円")
    shown["実績金額(円)"] = shown["実績"].map(lambda x: f"{x:,.0f} 円")
    shown["残額(円)"] = shown["残額"].map(lambda x: f"{x:,.0f} 円")
    shown = shown[["対象項目", "期間表示", "予算金額(円)", "実績金額(円)", "残額(円)"]]
    st.markdown("### 予実サマリー表")
    st.dataframe(
        shown.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "対象項目": st.column_config.TextColumn("対象項目"),
            "期間表示": st.column_config.TextColumn("期間表示"),
            "予算金額(円)": st.column_config.TextColumn("予算金額(円)"),
            "実績金額(円)": st.column_config.TextColumn("実績金額(円)"),
            "残額(円)": st.column_config.TextColumn("残額(円)"),
        },
    )

    render_item_bar_chart(summary)


if __name__ == "__main__":
    main()

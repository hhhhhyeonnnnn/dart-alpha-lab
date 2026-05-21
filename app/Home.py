from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path("data/processed/factor_forward_returns_3m.csv")


st.set_page_config(
    page_title="DART Alpha Lab",
    page_icon="📈",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error(
            "factor_forward_returns_3m.csv 파일이 없습니다. "
            "먼저 forward_return.py를 실행하세요."
        )
        return pd.DataFrame()

    df = pd.read_csv(
        DATA_PATH,
        dtype={
            "corp_code": str,
            "stock_code": str,
        },
    )

    df["year"] = df["year"].astype(int)
    df["return_3m"] = pd.to_numeric(df["return_3m"], errors="coerce")
    df["operating_margin"] = pd.to_numeric(df["operating_margin"], errors="coerce")
    df["prev_operating_margin"] = pd.to_numeric(df["prev_operating_margin"], errors="coerce")

    df["return_3m_pct"] = df["return_3m"] * 100
    df["operating_margin_pct"] = df["operating_margin"] * 100
    df["prev_operating_margin_pct"] = df["prev_operating_margin"] * 100

    # CSV에서 True/False가 문자열로 읽힐 수 있어서 정리
    df["margin_improved"] = df["margin_improved"].astype(str)

    return df


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.2f}%"


def main():
    st.title("📈 DART Alpha Lab")
    st.caption("OpenDART 재무데이터 기반 영업이익률 개선 팩터 분석 대시보드")

    df = load_data()

    if df.empty:
        st.stop()

    st.sidebar.header("필터")

    years = sorted(df["year"].dropna().unique())
    selected_years = st.sidebar.multiselect(
        "분석 연도",
        options=years,
        default=years,
    )

    companies = sorted(df["corp_name"].dropna().unique())
    selected_companies = st.sidebar.multiselect(
        "기업 선택",
        options=companies,
        default=companies,
    )

    filtered = df[
        (df["year"].isin(selected_years))
        & (df["corp_name"].isin(selected_companies))
        & (df["margin_improved"].isin(["True", "False"]))
    ].copy()

    st.subheader("1. 전체 요약")

    if filtered.empty:
        st.warning("필터 조건에 맞는 데이터가 없습니다.")
        st.stop()

    improved_df = filtered[filtered["margin_improved"] == "True"]
    not_improved_df = filtered[filtered["margin_improved"] == "False"]

    improved_mean = improved_df["return_3m"].mean()
    not_improved_mean = not_improved_df["return_3m"].mean()
    diff = improved_mean - not_improved_mean

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("분석 데이터 수", f"{len(filtered)}개")
    col2.metric("개선 기업 평균 3개월 수익률", format_pct(improved_mean * 100))
    col3.metric("미개선 기업 평균 3개월 수익률", format_pct(not_improved_mean * 100))
    col4.metric("성과 차이", f"{diff * 100:.2f}%p")

    st.divider()

    st.subheader("2. 영업이익률 개선 여부별 3개월 수익률")

    summary = (
        filtered.groupby("margin_improved")["return_3m_pct"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )

    summary["margin_improved"] = summary["margin_improved"].replace(
        {
            "True": "개선",
            "False": "미개선",
        }
    )

    fig_bar = px.bar(
        summary,
        x="margin_improved",
        y="mean",
        text="mean",
        title="개선 여부별 평균 3개월 수익률",
        labels={
            "margin_improved": "영업이익률 개선 여부",
            "mean": "평균 3개월 수익률(%)",
        },
    )

    fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.dataframe(
        summary.rename(
            columns={
                "margin_improved": "구분",
                "count": "개수",
                "mean": "평균 수익률(%)",
                "median": "중앙값(%)",
                "min": "최소값(%)",
                "max": "최대값(%)",
            }
        ),
        use_container_width=True,
    )

    st.divider()

    st.subheader("3. 연도별 성과 비교")

    yearly = (
        filtered.groupby(["year", "margin_improved"])["return_3m_pct"]
        .mean()
        .reset_index()
    )

    yearly["margin_improved"] = yearly["margin_improved"].replace(
        {
            "True": "개선",
            "False": "미개선",
        }
    )

    fig_yearly = px.line(
        yearly,
        x="year",
        y="return_3m_pct",
        color="margin_improved",
        markers=True,
        title="연도별 평균 3개월 수익률",
        labels={
            "year": "연도",
            "return_3m_pct": "평균 3개월 수익률(%)",
            "margin_improved": "구분",
        },
    )

    st.plotly_chart(fig_yearly, use_container_width=True)

    st.divider()

    st.subheader("4. 기업별 상세 결과")

    display_cols = [
        "corp_name",
        "stock_code",
        "year",
        "operating_margin_pct",
        "prev_operating_margin_pct",
        "margin_improved",
        "signal_date",
        "exit_date",
        "entry_price",
        "exit_price",
        "return_3m_pct",
    ]

    table = filtered[display_cols].copy()

    table["margin_improved"] = table["margin_improved"].replace(
        {
            "True": "개선",
            "False": "미개선",
        }
    )

    table = table.rename(
        columns={
            "corp_name": "기업명",
            "stock_code": "종목코드",
            "year": "연도",
            "operating_margin_pct": "영업이익률(%)",
            "prev_operating_margin_pct": "전년 영업이익률(%)",
            "margin_improved": "개선 여부",
            "signal_date": "진입일",
            "exit_date": "청산일",
            "entry_price": "진입가",
            "exit_price": "청산가",
            "return_3m_pct": "3개월 수익률(%)",
        }
    )

    st.dataframe(
        table.sort_values("3개월 수익률(%)", ascending=False),
        use_container_width=True,
    )

    st.divider()

    st.subheader("5. 해석")

    st.markdown(
        f"""
        현재 필터 기준에서 **영업이익률 개선 기업**의 평균 3개월 수익률은  
        **{format_pct(improved_mean * 100)}**이고, **미개선 기업**의 평균 3개월 수익률은  
        **{format_pct(not_improved_mean * 100)}**입니다.

        두 그룹의 차이는 **{diff * 100:.2f}%p**입니다.

        단, 현재 분석은 소수 기업을 대상으로 한 MVP 테스트이며,  
        실제 투자 전략으로 판단하려면 분석 대상 기업 수 확대, 거래비용 반영, 생존편향 제거,  
        공시일 기준 정교화가 필요합니다.
        """
    )


if __name__ == "__main__":
    main()
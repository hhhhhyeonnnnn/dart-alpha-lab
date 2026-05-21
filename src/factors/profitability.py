from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/financials_key_accounts_2021_2024.csv")
OUTPUT_PATH = Path("data/processed/profitability_factors_2021_2024.csv")


def load_financials() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"{INPUT_PATH} 파일이 없습니다. "
            "먼저 batch_financial_collector.py를 실행하세요."
        )

    df = pd.read_csv(
        INPUT_PATH,
        dtype={
            "corp_code": str,
            "stock_code": str,
            "year": str,
        },
    )

    return df


def to_numeric_amount(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace({"": None, "nan": None, "None": None})
        .astype(float)
    )


def filter_income_statement(df: pd.DataFrame) -> pd.DataFrame:
    """
    매출액과 영업이익은 손익계산서 계정이므로,
    재무상태표/현금흐름표 쪽 계정이 섞이지 않게 1차 필터링.
    """
    if "sj_nm" not in df.columns:
        return df

    income_df = df[df["sj_nm"].astype(str).str.contains("손익", na=False)].copy()

    if income_df.empty:
        return df

    return income_df


def pick_account_amount(
    group: pd.DataFrame,
    include_keywords: list[str],
    exclude_keywords: list[str] | None = None,
) -> float | None:
    """
    기업-연도 그룹에서 원하는 계정명을 찾아 금액 하나를 선택.
    후보가 여러 개면 절댓값이 가장 큰 금액을 사용.
    """

    if exclude_keywords is None:
        exclude_keywords = []

    account_names = group["account_nm"].astype(str)

    include_mask = pd.Series(False, index=group.index)
    for keyword in include_keywords:
        include_mask |= account_names.str.contains(keyword, na=False, regex=False)

    exclude_mask = pd.Series(False, index=group.index)
    for keyword in exclude_keywords:
        exclude_mask |= account_names.str.contains(keyword, na=False, regex=False)

    candidates = group[include_mask & ~exclude_mask].copy()

    if candidates.empty:
        return None

    if "thstrm_amount" not in candidates.columns:
        return None

    candidates["amount"] = to_numeric_amount(candidates["thstrm_amount"])
    candidates = candidates.dropna(subset=["amount"])

    if candidates.empty:
        return None

    candidates["abs_amount"] = candidates["amount"].abs()

    selected = candidates.sort_values("abs_amount", ascending=False).iloc[0]

    return float(selected["amount"])


def build_profitability_factors(df: pd.DataFrame) -> pd.DataFrame:
    df = filter_income_statement(df)

    results = []

    group_cols = ["corp_code", "stock_code", "corp_name", "year"]

    for keys, group in df.groupby(group_cols):
        corp_code, stock_code, corp_name, year = keys

        revenue = pick_account_amount(
            group,
            include_keywords=[
                "매출액",
                "영업수익",
                "수익(매출액)",
            ],
            exclude_keywords=[
                "기타수익",
                "금융수익",
                "이자수익",
                "배당수익",
                "외환",
                "처분이익",
                "평가이익",
            ],
        )

        operating_income = pick_account_amount(
            group,
            include_keywords=[
                "영업이익",
            ],
            exclude_keywords=[],
        )

        if revenue is None or operating_income is None:
            continue

        if revenue == 0:
            operating_margin = None
        else:
            operating_margin = operating_income / revenue

        results.append(
            {
                "corp_code": corp_code,
                "stock_code": stock_code,
                "corp_name": corp_name,
                "year": int(year),
                "revenue": revenue,
                "operating_income": operating_income,
                "operating_margin": operating_margin,
            }
        )

    factor_df = pd.DataFrame(results)

    if factor_df.empty:
        return factor_df

    factor_df = factor_df.sort_values(["stock_code", "year"]).reset_index(drop=True)

    factor_df["prev_operating_margin"] = (
        factor_df.groupby("stock_code")["operating_margin"].shift(1)
    )

    factor_df["margin_improved"] = (
        factor_df["operating_margin"] > factor_df["prev_operating_margin"]
    ).astype("boolean")

    factor_df.loc[
        factor_df["prev_operating_margin"].isna(),
        "margin_improved",
    ] = pd.NA

    return factor_df


def main():
    df = load_financials()

    factor_df = build_profitability_factors(df)

    if factor_df.empty:
        print("계산된 팩터 데이터가 없습니다.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    factor_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("영업이익률 팩터 계산 완료!")
    print(f"저장 위치: {OUTPUT_PATH}")
    print(f"전체 행 개수: {len(factor_df)}")
    print(f"기업 수: {factor_df['corp_name'].nunique()}")

    print("\n미리보기:")
    preview_cols = [
        "corp_name",
        "stock_code",
        "year",
        "revenue",
        "operating_income",
        "operating_margin",
        "prev_operating_margin",
        "margin_improved",
    ]
    print(factor_df[preview_cols].head(30))


if __name__ == "__main__":
    main()
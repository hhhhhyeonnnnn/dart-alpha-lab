from pathlib import Path

import pandas as pd


FACTOR_PATH = Path("data/processed/profitability_factors_2021_2024.csv")
PRICE_PATH = Path("data/processed/prices_2020_today.csv")
FILING_PATH = Path("data/processed/annual_report_filing_dates_2021_2024.csv")
OUTPUT_PATH = Path("data/processed/factor_forward_returns_3m.csv")


HOLDING_DAYS = 63


def parse_bool(value):
    if pd.isna(value):
        return pd.NA

    if value is True or value == "True" or value == "true":
        return True

    if value is False or value == "False" or value == "false":
        return False

    return pd.NA


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not FACTOR_PATH.exists():
        raise FileNotFoundError(f"{FACTOR_PATH} 파일이 없습니다.")

    if not PRICE_PATH.exists():
        raise FileNotFoundError(f"{PRICE_PATH} 파일이 없습니다.")

    if not FILING_PATH.exists():
        raise FileNotFoundError(
            f"{FILING_PATH} 파일이 없습니다. "
            "먼저 filing_date_collector.py를 실행하세요."
        )

    factors = pd.read_csv(
        FACTOR_PATH,
        dtype={
            "corp_code": str,
            "stock_code": str,
        },
    )

    prices = pd.read_csv(
        PRICE_PATH,
        dtype={
            "stock_code": str,
        },
    )

    filings = pd.read_csv(
        FILING_PATH,
        dtype={
            "corp_code": str,
            "stock_code": str,
        },
    )

    factors["stock_code"] = factors["stock_code"].astype(str).str.zfill(6)
    prices["stock_code"] = prices["stock_code"].astype(str).str.zfill(6)
    filings["stock_code"] = filings["stock_code"].astype(str).str.zfill(6)

    factors["year"] = factors["year"].astype(int)
    filings["year"] = filings["year"].astype(int)

    factors["margin_improved"] = factors["margin_improved"].apply(parse_bool)

    prices["date"] = pd.to_datetime(prices["date"])
    filings["filing_date"] = pd.to_datetime(filings["filing_date"])

    factors_with_filing = factors.merge(
        filings[
            [
                "corp_code",
                "stock_code",
                "year",
                "filing_date",
                "rcept_no",
                "report_nm",
            ]
        ],
        on=["corp_code", "stock_code", "year"],
        how="left",
    )

    return factors_with_filing, prices


def calculate_forward_return(
    stock_prices: pd.DataFrame,
    filing_date: pd.Timestamp,
    holding_days: int = HOLDING_DAYS,
) -> dict | None:
    """
    실제 공시일 다음 거래일에 진입하고,
    holding_days 거래일 후 청산한다.

    공시가 장중/장마감 이후 언제 나왔는지까지는 고려하지 않기 위해
    보수적으로 '공시일 이후 첫 거래일'을 진입일로 사용한다.
    """

    if pd.isna(filing_date):
        return None

    stock_prices = stock_prices.sort_values("date").reset_index(drop=True)

    after_filing = stock_prices[stock_prices["date"] > filing_date].copy()

    if len(after_filing) <= holding_days:
        return None

    entry = after_filing.iloc[0]
    exit_ = after_filing.iloc[holding_days]

    entry_price = entry["close"]
    exit_price = exit_["close"]

    if pd.isna(entry_price) or pd.isna(exit_price) or entry_price == 0:
        return None

    forward_return = (exit_price / entry_price) - 1

    return {
        "filing_date": filing_date,
        "signal_date": entry["date"],
        "exit_date": exit_["date"],
        "entry_price": entry_price,
        "exit_price": exit_price,
        "return_3m": forward_return,
    }


def build_forward_returns() -> pd.DataFrame:
    factors, prices = load_data()

    results = []

    for _, row in factors.iterrows():
        stock_code = row["stock_code"]

        stock_prices = prices[prices["stock_code"] == stock_code].copy()

        if stock_prices.empty:
            continue

        return_info = calculate_forward_return(
            stock_prices=stock_prices,
            filing_date=row["filing_date"],
            holding_days=HOLDING_DAYS,
        )

        if return_info is None:
            continue

        result = row.to_dict()
        result.update(return_info)

        results.append(result)

    return pd.DataFrame(results)


def print_summary(result_df: pd.DataFrame) -> None:
    if result_df.empty:
        print("분석할 결과가 없습니다.")
        return

    analysis_df = result_df.dropna(subset=["margin_improved", "return_3m"]).copy()

    if analysis_df.empty:
        print("margin_improved 기준으로 분석할 데이터가 없습니다.")
        return

    summary = (
        analysis_df
        .groupby("margin_improved")["return_3m"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )

    print("\n영업이익률 개선 여부별 3개월 수익률 요약:")
    print(summary)

    true_mean = summary.loc[
        summary["margin_improved"] == True,
        "mean",
    ]

    false_mean = summary.loc[
        summary["margin_improved"] == False,
        "mean",
    ]

    if not true_mean.empty and not false_mean.empty:
        diff = true_mean.iloc[0] - false_mean.iloc[0]
        print(f"\n개선 기업 평균 - 미개선 기업 평균: {diff * 100:.2f}%p")


def main():
    result_df = build_forward_returns()

    if result_df.empty:
        print("계산된 미래 수익률 데이터가 없습니다.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("3개월 미래 수익률 계산 완료!")
    print(f"저장 위치: {OUTPUT_PATH}")
    print(f"전체 행 개수: {len(result_df)}")
    print(f"기업 수: {result_df['corp_name'].nunique()}")

    preview_cols = [
        "corp_name",
        "stock_code",
        "year",
        "operating_margin",
        "prev_operating_margin",
        "margin_improved",
        "filing_date",
        "signal_date",
        "exit_date",
        "entry_price",
        "exit_price",
        "return_3m",
        "report_nm",
    ]

    existing_cols = [col for col in preview_cols if col in result_df.columns]

    print("\n미리보기:")
    print(result_df[existing_cols].head(30))

    print_summary(result_df)


if __name__ == "__main__":
    main()
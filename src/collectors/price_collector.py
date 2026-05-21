from pathlib import Path
from datetime import date, timedelta
import time

import pandas as pd
import yfinance as yf


FACTOR_PATH = Path("data/processed/profitability_factors_2021_2024.csv")
OUTPUT_PATH = Path("data/processed/prices_2020_today.csv")


def normalize_stock_code(stock_code) -> str:
    return str(stock_code).zfill(6)


def load_factor_stocks() -> list[str]:
    if not FACTOR_PATH.exists():
        raise FileNotFoundError(
            f"{FACTOR_PATH} 파일이 없습니다. 먼저 profitability.py를 실행하세요."
        )

    df = pd.read_csv(FACTOR_PATH, dtype={"stock_code": str})
    stock_codes = sorted(df["stock_code"].dropna().unique())

    return [normalize_stock_code(code) for code in stock_codes]


def download_single_stock_price(
    stock_code: str,
    start_date: str = "2020-01-01",
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    한국 주식은 Yahoo Finance에서 보통
    KOSPI: 005930.KS
    KOSDAQ: 035720.KQ
    형태로 조회한다.

    시장 구분 정보가 아직 없으므로 .KS 먼저 시도하고,
    실패하면 .KQ를 시도한다.
    """

    if end_date is None:
        end_date = (date.today() + timedelta(days=1)).isoformat()

    stock_code = normalize_stock_code(stock_code)

    yahoo_tickers = [
        f"{stock_code}.KS",
        f"{stock_code}.KQ",
    ]

    for yahoo_ticker in yahoo_tickers:
        try:
            print(f"{yahoo_ticker} 주가 다운로드 시도...")

            ticker = yf.Ticker(yahoo_ticker)
            hist = ticker.history(
                start=start_date,
                end=end_date,
                interval="1d",
                auto_adjust=False,
            )

            if hist.empty:
                print(f"  -> 데이터 없음: {yahoo_ticker}")
                continue

            hist = hist.reset_index()

            date_col = "Date" if "Date" in hist.columns else "Datetime"

            hist = hist.rename(
                columns={
                    date_col: "date",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            )

            hist["date"] = pd.to_datetime(hist["date"]).dt.date
            hist["stock_code"] = stock_code
            hist["yahoo_ticker"] = yahoo_ticker

            keep_cols = [
                "stock_code",
                "yahoo_ticker",
                "date",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
            ]

            existing_cols = [col for col in keep_cols if col in hist.columns]

            result = hist[existing_cols].copy()
            print(f"  -> 성공: {yahoo_ticker}, {len(result)}개 일봉")

            return result

        except Exception as e:
            print(f"  -> 실패: {yahoo_ticker}, {e}")

    return pd.DataFrame()


def collect_prices() -> pd.DataFrame:
    stock_codes = load_factor_stocks()

    all_prices = []

    for idx, stock_code in enumerate(stock_codes, start=1):
        print(f"\n[{idx}/{len(stock_codes)}] {stock_code} 수집 중")

        price_df = download_single_stock_price(stock_code)

        if not price_df.empty:
            all_prices.append(price_df)

        time.sleep(0.3)

    if not all_prices:
        return pd.DataFrame()

    return pd.concat(all_prices, ignore_index=True)


def main():
    prices = collect_prices()

    if prices.empty:
        print("수집된 주가 데이터가 없습니다.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("\n주가 데이터 수집 완료!")
    print(f"저장 위치: {OUTPUT_PATH}")
    print(f"전체 행 개수: {len(prices)}")
    print(f"종목 수: {prices['stock_code'].nunique()}")

    print("\n미리보기:")
    print(prices.head(20))


if __name__ == "__main__":
    main()
from pathlib import Path
import time

import pandas as pd
import requests

from src.config import DART_API_KEY


FACTOR_PATH = Path("data/processed/profitability_factors_2021_2024.csv")
OUTPUT_PATH = Path("data/processed/annual_report_filing_dates_2021_2024.csv")

DISCLOSURE_LIST_URL = "https://opendart.fss.or.kr/api/list.json"


def normalize_stock_code(stock_code) -> str:
    return str(stock_code).zfill(6)


def load_factor_companies() -> pd.DataFrame:
    if not FACTOR_PATH.exists():
        raise FileNotFoundError(
            f"{FACTOR_PATH} 파일이 없습니다. 먼저 profitability.py를 실행하세요."
        )

    df = pd.read_csv(
        FACTOR_PATH,
        dtype={
            "corp_code": str,
            "stock_code": str,
        },
    )

    df["stock_code"] = df["stock_code"].apply(normalize_stock_code)
    df["year"] = df["year"].astype(int)

    companies = (
        df[["corp_code", "stock_code", "corp_name", "year"]]
        .drop_duplicates()
        .sort_values(["stock_code", "year"])
        .reset_index(drop=True)
    )

    return companies


def fetch_annual_report_filing(
    corp_code: str,
    fiscal_year: int,
) -> dict | None:
    """
    특정 기업의 특정 사업연도 사업보고서 접수일을 찾는다.

    예:
    fiscal_year=2021이면 보통 2022년 1월~5월 사이에
    2021년 사업보고서가 제출된다.
    """

    search_year = fiscal_year + 1

    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bgn_de": f"{search_year}0101",
        "end_de": f"{search_year}0531",
        "pblntf_ty": "A",
        "pblntf_detail_ty": "A001",
        "sort": "date",
        "sort_mth": "asc",
        "page_no": "1",
        "page_count": "100",
    }

    response = requests.get(DISCLOSURE_LIST_URL, params=params, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(f"요청 실패: status_code={response.status_code}")

    data = response.json()

    status = data.get("status")
    message = data.get("message")

    if status == "013":
        return None

    if status != "000":
        raise RuntimeError(f"DART API 오류: {status} / {message}")

    rows = data.get("list", [])

    if not rows:
        return None

    df = pd.DataFrame(rows)

    if df.empty:
        return None

    # 사업보고서만 필터링
    df = df[df["report_nm"].astype(str).str.contains("사업보고서", na=False)].copy()

    if df.empty:
        return None

    # [기재정정], [첨부정정] 같은 정정 보고서는 제외하고 최초 제출 보고서를 우선 사용
    original_df = df[
        ~df["report_nm"].astype(str).str.startswith("[")
        ].copy()

    if not original_df.empty:
        df = original_df

    df["rcept_dt"] = pd.to_datetime(df["rcept_dt"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["rcept_dt"])

    if df.empty:
        return None

    selected = df.sort_values("rcept_dt", ascending=True).iloc[0]

    return {
        "filing_date": selected["rcept_dt"].date().isoformat(),
        "rcept_no": selected.get("rcept_no"),
        "report_nm": selected.get("report_nm"),
    }


def collect_filing_dates() -> pd.DataFrame:
    companies = load_factor_companies()

    results = []

    total = len(companies)

    for idx, row in companies.iterrows():
        corp_code = row["corp_code"]
        stock_code = row["stock_code"]
        corp_name = row["corp_name"]
        year = int(row["year"])

        print(f"[{idx + 1}/{total}] {corp_name} {year} 사업보고서 공시일 수집 중...")

        try:
            filing_info = fetch_annual_report_filing(
                corp_code=corp_code,
                fiscal_year=year,
            )

            if filing_info is None:
                print("  -> 공시일 데이터 없음")
                continue

            results.append(
                {
                    "corp_code": corp_code,
                    "stock_code": stock_code,
                    "corp_name": corp_name,
                    "year": year,
                    **filing_info,
                }
            )

            print(
                f"  -> 성공: {filing_info['filing_date']} / "
                f"{filing_info['report_nm']}"
            )

        except Exception as e:
            print(f"  -> 실패: {e}")

        time.sleep(0.3)

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


def main():
    result_df = collect_filing_dates()

    if result_df.empty:
        print("수집된 공시일 데이터가 없습니다.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("\n사업보고서 공시일 수집 완료!")
    print(f"저장 위치: {OUTPUT_PATH}")
    print(f"전체 행 개수: {len(result_df)}")
    print(f"기업 수: {result_df['corp_name'].nunique()}")

    print("\n미리보기:")
    print(result_df.head(30))


if __name__ == "__main__":
    main()
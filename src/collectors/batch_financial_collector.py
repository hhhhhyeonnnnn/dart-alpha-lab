import time
from pathlib import Path

import pandas as pd

from src.collectors.financial_collector import fetch_financial_statement, extract_key_accounts


YEARS = ["2021", "2022", "2023", "2024"]
REPORT_TYPE = "ANNUAL"
OUTPUT_DIR = Path("data/processed")

def load_companies(limit: int = 50) -> pd.DataFrame:
    """
    corp_codes.csv에서 분석 대상 기업을 불러온다.
    회사명보다 종목코드 기준으로 선택하는 것이 더 안정적이다.
    """
    corp_codes_path = OUTPUT_DIR / "corp_codes.csv"

    if not corp_codes_path.exists():
        raise FileNotFoundError(
            "data/processed/corp_codes.csv 파일이 없습니다. "
            "먼저 corp_code_collector.py를 실행하세요."
        )

    df = pd.read_csv(
        corp_codes_path,
        dtype={"corp_code": str, "stock_code": str}
    )

    df = df.dropna(subset=["corp_code", "stock_code"])
    df["stock_code"] = df["stock_code"].astype(str).str.zfill(6)
    df = df[df["stock_code"].str.strip() != ""]

    preferred_stock_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "005380",  # 현대자동차
        "000270",  # 기아
        "035420",  # NAVER
        "035720",  # 카카오
        "066570",  # LG전자
        "005490",  # POSCO홀딩스
        "006400",  # 삼성SDI
        "068270",  # 셀트리온
        "207940",  # 삼성바이오로직스
        "012330",  # 현대모비스
        "051910",  # LG화학
        "028260",  # 삼성물산
        "015760",  # 한국전력
        "030200",  # KT
        "096770",  # SK이노베이션
        "034730",  # SK
        "017670",  # SK텔레콤
        "018260",  # 삼성에스디에스
        "010130",  # 고려아연
        "003550",  # LG
        "009150",  # 삼성전기
        "086280",  # 현대글로비스
        "011200",  # HMM
        "034020",  # 두산에너빌리티
        "042700",  # 한미반도체
        "012450",  # 한화에어로스페이스
        "047050",  # 포스코인터내셔널
        "003670",  # 포스코퓨처엠
        "090430",  # 아모레퍼시픽
        "011780",  # 금호석유화학
        "010950",  # S-Oil
        "010140",  # 삼성중공업
        "329180",  # HD현대중공업
        "010120",  # LS ELECTRIC
        "011170",  # 롯데케미칼
        "036570",  # 엔씨소프트
        "251270",  # 넷마블
        "352820",  # 하이브
        "000720",  # 현대건설
        "009540",  # HD한국조선해양
        "267260",  # HD현대일렉트릭
        "241560",  # 두산밥캣
        "161390",  # 한국타이어앤테크놀로지
        "271560",  # 오리온
        "097950",  # CJ제일제당
        "128940",  # 한미약품
        "326030",  # SK바이오팜
        "180640",  # 한진칼
    ]
    selected_codes = preferred_stock_codes[:limit]

    selected_df = df[df["stock_code"].isin(selected_codes)].copy()

    found_codes = set(selected_df["stock_code"])
    missing_codes = [code for code in selected_codes if code not in found_codes]

    print(f"선택 기업 수: {len(selected_df)}")
    if missing_codes:
        print(f"corp_codes.csv에서 찾지 못한 종목코드: {missing_codes}")

    return selected_df


def fetch_company_year_financials(company: pd.Series, year: str) -> pd.DataFrame:
    """
    특정 기업의 특정 연도 재무제표 수집.
    연결재무제표 CFS를 먼저 시도하고,
    실패하면 개별재무제표 OFS를 시도.
    """
    corp_code = company["corp_code"]
    stock_code = company["stock_code"]
    corp_name = company["corp_name"]

    for fs_div in ["CFS", "OFS"]:
        try:
            df = fetch_financial_statement(
                corp_code=corp_code,
                bsns_year=year,
                report_type=REPORT_TYPE,
                fs_div=fs_div,
            )

            if df.empty:
                continue

            key_df = extract_key_accounts(df)

            if key_df.empty:
                continue

            key_df["corp_code"] = corp_code
            key_df["stock_code"] = stock_code
            key_df["corp_name"] = corp_name
            key_df["year"] = year
            key_df["fs_div_used"] = fs_div

            return key_df

        except Exception as e:
            print(f"[실패] {corp_name} {year} {fs_div}: {e}")
            continue

    return pd.DataFrame()


def collect_batch_financials(limit: int = 30) -> pd.DataFrame:
    companies = load_companies(limit=limit)

    all_data = []

    total_tasks = len(companies) * len(YEARS)
    current_task = 0

    for _, company in companies.iterrows():
        corp_name = company["corp_name"]

        for year in YEARS:
            current_task += 1
            print(f"[{current_task}/{total_tasks}] {corp_name} {year} 재무제표 수집 중...")

            result = fetch_company_year_financials(company, year)

            if not result.empty:
                all_data.append(result)
                print(f"  -> 성공: {len(result)}개 계정")
            else:
                print("  -> 데이터 없음")

            time.sleep(0.3)

    if not all_data:
        return pd.DataFrame()

    final_df = pd.concat(all_data, ignore_index=True)
    return final_df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    final_df = collect_batch_financials(limit=50)

    if final_df.empty:
        print("수집된 데이터가 없습니다.")
        return

    output_path = OUTPUT_DIR / "financials_key_accounts_2021_2024.csv"
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\n저장 완료!")
    print(f"파일 위치: {output_path}")
    print(f"전체 행 개수: {len(final_df)}")
    print(f"기업 수: {final_df['corp_name'].nunique()}")
    print(f"연도 수: {final_df['year'].nunique()}")

    preview_cols = [
        "corp_name",
        "stock_code",
        "year",
        "fs_div_used",
        "sj_nm",
        "account_nm",
        "thstrm_amount",
        "currency",
    ]

    existing_cols = [col for col in preview_cols if col in final_df.columns]
    print("\n미리보기:")
    print(final_df[existing_cols].head(20))


if __name__ == "__main__":
    main()
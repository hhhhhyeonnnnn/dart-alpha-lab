import pandas as pd
import requests

from src.config import DART_API_KEY


FINANCIAL_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

REPORT_CODES = {
    "1Q": "11013",
    "HALF": "11012",
    "3Q": "11014",
    "ANNUAL": "11011",
}


def fetch_financial_statement(
    corp_code: str,
    bsns_year: str,
    report_type: str = "ANNUAL",
    fs_div: str = "CFS",
) -> pd.DataFrame:
    """
    corp_code: DART 기업 고유번호
    bsns_year: 사업연도, 예: "2024"
    report_type: 1Q / HALF / 3Q / ANNUAL
    fs_div: CFS 연결재무제표, OFS 개별재무제표
    """

    if report_type not in REPORT_CODES:
        raise ValueError(f"report_type은 {list(REPORT_CODES.keys())} 중 하나여야 합니다.")

    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": REPORT_CODES[report_type],
        "fs_div": fs_div,
    }

    response = requests.get(FINANCIAL_URL, params=params, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(f"요청 실패: status_code={response.status_code}")

    data = response.json()

    status = data.get("status")
    message = data.get("message")

    if status != "000":
        raise RuntimeError(f"DART API 오류: {status} / {message}")

    rows = data.get("list", [])

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df


def clean_amount(value):
    if value is None:
        return None

    value = str(value).replace(",", "").strip()

    if value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def extract_key_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    초반 MVP에서 쓸 핵심 계정만 추출.
    회사마다 계정명이 조금씩 다를 수 있어서 일단 contains 방식 사용.
    """

    if df.empty:
        return df

    target_keywords = [
        "매출액",
        "수익",
        "영업이익",
        "당기순이익",
        "자산총계",
        "부채총계",
        "자본총계",
    ]

    pattern = "|".join(target_keywords)

    result = df[df["account_nm"].str.contains(pattern, na=False)].copy()

    amount_columns = [
        "thstrm_amount",
        "thstrm_add_amount",
        "frmtrm_amount",
        "frmtrm_q_amount",
        "frmtrm_add_amount",
        "bfefrmtrm_amount",
    ]

    for col in amount_columns:
        if col in result.columns:
            result[col] = result[col].apply(clean_amount)

    return result


def main():
    corp_codes = pd.read_csv("data/processed/corp_codes.csv", dtype={"stock_code": str, "corp_code": str})

    samsung = corp_codes[corp_codes["corp_name"] == "삼성전자"].iloc[0]
    corp_code = samsung["corp_code"]

    print(f"삼성전자 corp_code: {corp_code}")

    df = fetch_financial_statement(
        corp_code=corp_code,
        bsns_year="2024",
        report_type="ANNUAL",
        fs_div="CFS",
    )

    key_df = extract_key_accounts(df)

    output_path = "data/processed/samsung_financial_2024.csv"
    key_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"저장 완료: {output_path}")
    print(key_df[["bsns_year", "sj_nm", "account_nm", "thstrm_amount", "currency"]].head(30))


if __name__ == "__main__":
    main()
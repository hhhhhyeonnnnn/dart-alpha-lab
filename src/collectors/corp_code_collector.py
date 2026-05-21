import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

import pandas as pd
import requests

from src.config import DART_API_KEY


CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"


def fetch_corp_code_zip() -> bytes:
    params = {
        "crtfc_key": DART_API_KEY
    }

    response = requests.get(CORP_CODE_URL, params=params, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(f"요청 실패: status_code={response.status_code}")

    content = response.content

    # 인증키 오류가 나면 ZIP이 아니라 XML 에러 메시지가 옴
    if content.strip().startswith(b"<?xml"):
        try:
            root = ET.fromstring(content)
            status = root.findtext("status")
            message = root.findtext("message")
            raise RuntimeError(f"DART API 오류: {status} / {message}")
        except ET.ParseError:
            raise RuntimeError("DART API 오류 응답을 파싱하지 못했습니다.")

    return content


def parse_corp_code_xml(zip_bytes: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        xml_filename = zf.namelist()[0]
        xml_data = zf.read(xml_filename)

    root = ET.fromstring(xml_data)

    rows = []

    for item in root.findall("list"):
        rows.append({
            "corp_code": item.findtext("corp_code"),
            "corp_name": item.findtext("corp_name"),
            "corp_eng_name": item.findtext("corp_eng_name"),
            "stock_code": item.findtext("stock_code"),
            "modify_date": item.findtext("modify_date"),
        })

    df = pd.DataFrame(rows)

    # 종목코드가 있는 회사만 상장사로 간주
    df["stock_code"] = df["stock_code"].fillna("").str.strip()
    listed_df = df[df["stock_code"] != ""].copy()

    return listed_df


def save_corp_codes(df: pd.DataFrame, output_path: str = "data/processed/corp_codes.csv") -> None:
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {output_path}")
    print(f"상장사 개수: {len(df)}")


def main():
    print("OpenDART 기업코드 다운로드 중...")
    zip_bytes = fetch_corp_code_zip()

    print("기업코드 XML 파싱 중...")
    df = parse_corp_code_xml(zip_bytes)

    save_corp_codes(df)

    print("\n상위 10개 기업:")
    print(df.head(10))


if __name__ == "__main__":
    main()
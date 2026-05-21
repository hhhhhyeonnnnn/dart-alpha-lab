from src.collectors.corp_code_collector import main as collect_corp_codes
from src.collectors.financial_collector import main as collect_financials


def main():
    print("1. 기업코드 수집")
    collect_corp_codes()

    print("\n2. 삼성전자 재무제표 테스트 수집")
    collect_financials()


if __name__ == "__main__":
    main()
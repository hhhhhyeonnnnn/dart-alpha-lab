# DART Alpha Lab: OpenDART 기반 재무 팩터 퀀트 리서치

## 1. 프로젝트 소개

**DART Alpha Lab**은 OpenDART 재무제표 데이터를 활용하여 한국 상장기업의 재무 팩터와 이후 주가 수익률의 관계를 분석하는 퀀트 리서치 프로젝트입니다.

현재 MVP에서는 **영업이익률이 전년 대비 개선된 기업이 이후 3개월 동안 더 높은 수익률을 보였는가?**를 분석합니다.

---

## 2. 핵심 아이디어

본 프로젝트의 핵심 질문은 다음과 같습니다.

> 전년 대비 영업이익률이 개선된 기업은 이후 3개월 주가 수익률이 더 좋았을까?

이를 검증하기 위해 다음 과정을 거칩니다.

```text
OpenDART 기업코드 수집
→ 기업별 재무제표 수집
→ 매출액, 영업이익 추출
→ 영업이익률 계산
→ 전년 대비 개선 여부 판단
→ 주가 데이터 수집
→ 3개월 미래 수익률 계산
→ Streamlit 대시보드 시각화
```

---

## 3. 대시보드 미리보기

아래 이미지는 Streamlit 대시보드 예시입니다.

> 스크린샷 파일을 `assets/dashboard_summary.png` 경로에 넣으면 아래에 자동으로 표시됩니다.

![Dashboard Screenshot](assets/dashboard_summary.png)

---

## 4. 주요 기능

### 4.1 OpenDART 기업코드 수집

OpenDART API를 사용하여 한국 상장기업의 기업 고유번호, 종목코드, 기업명을 수집합니다.

수집 항목 예시:

- 기업 고유번호
- 종목코드
- 기업명
- 최종 변경일

---

### 4.2 재무제표 수집

기업별로 2021년부터 2024년까지의 사업보고서 재무제표를 수집합니다.

현재 MVP에서는 다음과 같은 주요 계정을 사용합니다.

- 매출액
- 영업이익
- 당기순이익
- 자산총계
- 부채총계
- 자본총계

---

### 4.3 영업이익률 팩터 계산

기업별, 연도별로 영업이익률을 계산합니다.

```text
영업이익률 = 영업이익 / 매출액
```

이후 전년 대비 영업이익률이 개선되었는지를 판단합니다.

```text
올해 영업이익률 > 전년 영업이익률
→ margin_improved = True
```

---

### 4.4 주가 데이터 수집

분석 대상 기업의 일별 주가 데이터를 수집합니다.

현재 MVP에서는 프로토타입 구현을 위해 `yfinance`를 사용합니다.

---

### 4.5 3개월 미래 수익률 계산

각 기업의 재무 팩터 발생 이후 3개월 수익률을 계산합니다.

현재 MVP에서는 사업보고서 반영 시점을 단순화하여 다음 해 4월 1일을 진입 기준일로 설정했습니다.

예시:

```text
2021년 실적 → 2022년 4월 1일 진입
2022년 실적 → 2023년 4월 1일 진입
2023년 실적 → 2024년 4월 1일 진입
```

3개월 수익률 계산식은 다음과 같습니다.

```text
3개월 수익률 = 63거래일 후 종가 / 진입일 종가 - 1
```

---

### 4.6 Streamlit 대시보드

분석 결과를 Streamlit 대시보드로 시각화합니다.

대시보드에서 확인할 수 있는 내용:

- 분석 데이터 수
- 영업이익률 개선 기업의 평균 3개월 수익률
- 영업이익률 미개선 기업의 평균 3개월 수익률
- 두 그룹 간 성과 차이
- 연도별 수익률 비교
- 기업별 상세 결과표

---

## 5. 프로젝트 구조

```text
dart-alpha-lab/
│
├── app/
│   └── Home.py
│
├── assets/
│   └── dashboard_summary.png
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── collectors/
│   │   ├── corp_code_collector.py
│   │   ├── financial_collector.py
│   │   ├── batch_financial_collector.py
│   │   └── price_collector.py
│   │
│   ├── factors/
│   │   └── profitability.py
│   │
│   └── research/
│       └── forward_return.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 6. 사용 기술

- Python
- pandas
- requests
- python-dotenv
- yfinance
- Streamlit
- Plotly
- OpenDART API

---

## 7. 실행 방법

### 7.1 프로젝트 클론

```bash
git clone https://github.com/your-username/dart-alpha-lab.git
cd dart-alpha-lab
```

> `your-username` 부분은 본인의 GitHub 아이디로 변경합니다.

---

### 7.2 가상환경 생성 및 실행

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

---

### 7.3 라이브러리 설치

```bash
python -m pip install -r requirements.txt
```

---

### 7.4 환경변수 설정

프로젝트 최상위 폴더에 `.env` 파일을 생성하고 OpenDART API 키를 입력합니다.

```env
DART_API_KEY=your_dart_api_key
```

`.env` 파일은 API 키가 포함되어 있으므로 GitHub에 업로드하지 않습니다.

---

## 8. 데이터 수집 및 분석 실행 순서

### 8.1 기업코드 수집

```bash
python -m src.collectors.corp_code_collector
```

생성 파일:

```text
data/processed/corp_codes.csv
```

---

### 8.2 여러 기업 재무제표 수집

```bash
python -m src.collectors.batch_financial_collector
```

생성 파일:

```text
data/processed/financials_key_accounts_2021_2024.csv
```

---

### 8.3 영업이익률 팩터 계산

```bash
python -m src.factors.profitability
```

생성 파일:

```text
data/processed/profitability_factors_2021_2024.csv
```

---

### 8.4 주가 데이터 수집

```bash
python -m src.collectors.price_collector
```

생성 파일:

```text
data/processed/prices_2020_today.csv
```

---

### 8.5 3개월 미래 수익률 계산

```bash
python -m src.research.forward_return
```

생성 파일:

```text
data/processed/factor_forward_returns_3m.csv
```

---

### 8.6 대시보드 실행

```bash
python -m streamlit run app/Home.py
```

---

## 9. 현재 MVP 결과

현재 MVP에서는 일부 대형주를 대상으로 분석을 진행했습니다.

분석 결과, 영업이익률이 전년 대비 개선된 기업의 이후 3개월 평균 수익률이 미개선 기업보다 높게 나타났습니다.

예시 결과:

```text
개선 기업 평균 수익률 - 미개선 기업 평균 수익률 = 약 9.48%p
```

단, 현재 분석은 소수 기업을 대상으로 한 MVP 테스트이므로 이 결과를 일반적인 투자 전략의 성과로 단정할 수는 없습니다.

---

## 10. 프로젝트 한계점

현재 MVP에는 다음과 같은 한계가 있습니다.

### 10.1 표본 수 부족

현재는 일부 대형주만 대상으로 테스트했습니다.  
향후 KOSPI, KOSDAQ 전체 기업으로 분석 대상을 확장해야 합니다.

### 10.2 공시일 기준 단순화

현재는 사업보고서 반영 시점을 다음 해 4월 1일로 단순 설정했습니다.  
실제 분석에서는 기업별 사업보고서 공시일을 기준으로 다음 거래일에 진입하는 방식이 더 정확합니다.

### 10.3 생존편향 가능성

현재 수집 가능한 상장기업 위주로 분석하기 때문에 과거 상장폐지 기업이 제외될 수 있습니다.

### 10.4 거래비용 미반영

현재 수익률 계산에는 거래수수료, 세금, 슬리피지 등이 반영되어 있지 않습니다.

### 10.5 데이터 소스 한계

주가 데이터는 MVP 구현을 위해 yfinance를 사용했습니다.  
향후 KRX 또는 증권사 API 기반 데이터로 대체할 수 있습니다.

---

## 11. 향후 개선 방향

### 11.1 분석 대상 기업 확대

분석 대상을 다음 순서로 확장할 예정입니다.

- 대형주 10개
- 대형주 30개
- KOSPI 200
- KOSPI/KOSDAQ 전체

---

### 11.2 실제 공시일 기준 분석

OpenDART 공시검색 API를 활용하여 각 기업의 실제 사업보고서 제출일을 수집하고, 공시일 이후 다음 거래일 기준으로 수익률을 계산할 예정입니다.

---

### 11.3 추가 재무 팩터 개발

현재는 영업이익률 개선 여부만 사용하고 있지만, 향후 다음 팩터를 추가할 수 있습니다.

- 매출 성장률
- 영업이익 성장률
- ROE 개선
- 부채비율 감소
- 순이익률 개선
- 영업현금흐름 개선

---

### 11.4 보유기간 다양화

현재는 3개월 수익률만 계산합니다.

향후 다음 기간을 추가할 수 있습니다.

- 1개월 수익률
- 3개월 수익률
- 6개월 수익률
- 12개월 수익률

---

### 11.5 백테스트 전략화

단순 팩터 비교를 넘어 실제 포트폴리오 백테스트로 확장할 수 있습니다.

예시:

```text
매 분기 영업이익률 개선 기업 중 상위 N개 종목 매수
→ 동일가중 포트폴리오 구성
→ 3개월 보유 후 리밸런싱
→ 벤치마크와 성과 비교
```

---

### 11.6 대시보드 기능 확장

향후 Streamlit 대시보드에 다음 기능을 추가할 수 있습니다.

- 보유기간 선택
- 팩터 선택
- 기업 검색
- 수익률 분포 히스토그램
- 연도별 승률
- CSV 다운로드
- 종목별 상세 재무 추이

---

## 12. 프로젝트 의의

본 프로젝트는 단순한 주가 예측 모델이 아니라, 실제 공시 재무데이터를 기반으로 투자 아이디어를 검증하는 퀀트 리서치 파이프라인을 구현하는 데 목적이 있습니다.

이를 통해 다음 역량을 보여줄 수 있습니다.

- 금융 데이터 수집
- API 활용
- 재무제표 데이터 정제
- 팩터 설계
- 미래 수익률 계산
- 데이터 시각화
- 대시보드 구현
- 퀀트 리서치 사고방식

---

## 13. 주의사항

본 프로젝트는 학습 및 연구 목적의 프로젝트입니다.  
분석 결과는 투자 판단의 참고 자료로만 활용되어야 하며, 실제 투자 수익을 보장하지 않습니다.

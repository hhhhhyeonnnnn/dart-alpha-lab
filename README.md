# DART Alpha Lab

OpenDART 공시·재무 데이터를 기반으로 한국 상장기업의 재무 팩터와 향후 주가 수익률의 관계를 분석하는 퀀트 리서치 프로젝트입니다.

## MVP Goal

전년 동기 대비 영업이익률이 개선된 기업이 이후 3개월 동안 시장 대비 초과수익을 기록했는지 검증합니다.

## Current Progress

- [x] OpenDART API 연결
- [x] 상장기업 고유번호 수집
- [x] 단일 기업 재무제표 수집
- [ ] 핵심 재무계정 정제
- [ ] 영업이익률 팩터 계산
- [ ] 주가 데이터 결합
- [ ] 미래 수익률 계산
- [ ] Streamlit 대시보드 구현

## Tech Stack

- Python
- pandas
- OpenDART API
- Streamlit
- SQLite
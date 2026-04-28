# 발표 초안

## 1. 문제 정의

평균과 변동성 가정이 바뀔 때 1년 뒤 포트폴리오 가치 분포는 어떻게 달라지는가?

## 2. 데이터와 가정

- 합성 샘플 데이터: `data/sample/simulation_assumptions.csv`
- 원본 강의자료/코드 직접 사용 없음
- 재현 가능한 baseline 실행을 우선 구성

## 3. 방법

확률분포 가정이 금융 변수의 미래 범위와 손실확률에 미치는 영향을 시뮬레이션한다.

## 4. 현재 산출물

- 실행 스크립트: `python -m src.run_baseline`
- 결과 표: `outputs/tables/baseline_results.csv`

## 5. 후속 작업

- 실제 데이터 연결
- 민감도 분석
- 차트/보고서 산출
- 프로젝트별 상세 검증

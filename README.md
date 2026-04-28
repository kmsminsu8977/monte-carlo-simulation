# Monte Carlo Simulation

몬테카를로 시뮬레이션 프로젝트의 기본 연구 구조와 재현 가능한 baseline 산출물을 담은 저장소입니다.

**핵심 연구 질문**

> 평균과 변동성 가정이 바뀔 때 1년 뒤 포트폴리오 가치 분포는 어떻게 달라지는가?

## 작업 기준 문서

- `AGENTS.md`: 저장소 작업 기준과 품질 기준
- `SOURCE.md`: KAIST-DFMBA 참고 경로와 프로젝트별 컨텐츠 재구성 기준

## 저장소 구조

```text
monte-carlo-simulation/
├── src/                         # baseline 계산 로직과 실행 엔트리포인트
├── data/sample/                 # 합성 샘플 입력 데이터
├── docs/                        # 방법론과 해석 기준
├── notebooks/                   # 실행 흐름을 보여주는 최소 노트북
├── outputs/tables/              # 재현 가능한 결과 CSV
├── presentation/                # 발표/보고서 초안
└── references/                  # 재작성 개념 노트와 참고문헌 메모
```

## 빠른 시작

```bash
python -m src.run_baseline
```

실행 결과는 `outputs/tables/baseline_results.csv`에 저장됩니다.

## 구현 범위

- 로그정규 terminal value를 난수 시드와 함께 생성해 재현성을 확보한다.
- 평균, 분위수, 손실확률을 비교해 분포 가정의 영향을 직관적으로 설명한다.
- 입력값은 분포 가정의 차이를 비교하도록 구성한 합성 시나리오다.

## 주요 파일

- `src/monte_carlo_baseline.py`: 확률분포 가정이 금융 변수의 미래 범위와 손실확률에 미치는 영향을 시뮬레이션한다.
- `data/sample/simulation_assumptions.csv`: baseline 실행용 합성 입력값
- `docs/methodology.md`: 계산 절차, 입력/출력 정의, 해석상 주의점
- `outputs/tables/baseline_results.csv`: 현재 baseline 산출물

## 다음 확장 방향

- 실제 공개 데이터 또는 별도 수집 데이터 연결
- notebook 기반 탐색 분석 추가
- 차트와 표를 포함한 최종 보고서 작성
- 모델 검증, 민감도 분석, 비용/리스크 가정 보강

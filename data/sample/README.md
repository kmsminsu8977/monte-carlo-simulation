# Sample Data

이 폴더의 CSV 파일은 baseline 계산과 복습 자료 생성을 검증하기 위해 만든 합성 데이터입니다.

## `simulation_assumptions.csv`

- `scenario_id`
- `base_value`
- `annual_mu`
- `annual_sigma`
- `horizon_days`
- `n_paths`
- `seed`

## Usage

```bash
python -m src.run_baseline
```

## `review_scenarios.csv`

`review_scenarios.csv`는 평균, 변동성, 투자기간 차이를 비교하는 복습용 민감도 입력입니다. baseline 결과와 복습 자료를 구분하기 위해 별도 파일로 관리합니다.

- `scenario_id`: 복습 시나리오 이름
- `base_value`: 현재 포트폴리오 가치
- `annual_mu`: 연율 기대수익률 가정
- `annual_sigma`: 연율 변동성 가정
- `horizon_days`: 투자기간, 거래일 기준
- `n_paths`: 생성할 난수 경로 수
- `seed`: 재현 가능한 난수 seed
- `review_focus`: 해당 시나리오에서 집중해서 볼 해석 포인트

```bash
python -m src.generate_review_materials
```

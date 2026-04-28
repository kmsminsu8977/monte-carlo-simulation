# Sample Data

이 폴더의 `simulation_assumptions.csv`는 baseline 계산을 검증하기 위해 만든 합성 데이터입니다.

## Columns

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


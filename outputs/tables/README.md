# Output Tables

`baseline_results.csv`는 `python -m src.run_baseline` 실행으로 재생성할 수 있는 산출물입니다.

현재 결과는 `simulation_assumptions.csv` 합성 입력에 대한 baseline이며, 최종 투자 판단이나 통계 검정 결과로 사용하면 안 됩니다.

복습 자료는 다음 명령으로 재생성합니다.

```bash
python -m src.generate_review_materials
```

- `review_distribution_summary.csv`: 복습 시나리오별 terminal value 분포 요약
- `review_convergence_check.csv`: 경로 수별 평균 표준오차와 손실확률 점검표
- `review_flashcards.csv`: 개념 질문/답 카드
- `review_practice_questions.csv`: 자가 점검 문제와 답안

복습용 결과도 합성 입력 기반이므로, 실제 투자 판단이나 검증된 성과 주장으로 사용하지 않습니다.

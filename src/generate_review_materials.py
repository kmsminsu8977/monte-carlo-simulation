"""몬테카를로 시뮬레이션 복습 자료 생성기.

이 모듈은 `data/sample/review_scenarios.csv`에 정리한 합성 가정을 읽고,
복습에 바로 사용할 수 있는 표 자료를 `outputs/tables/`에 저장한다.

생성 산출물은 네 가지다.

1. `review_distribution_summary.csv`: 시나리오별 terminal value 분포 요약
2. `review_convergence_check.csv`: 경로 수가 늘어날 때 평균과 손실확률이 안정되는지 보는 표
3. `review_flashcards.csv`: 핵심 개념을 질문/답 형식으로 압축한 암기 카드
4. `review_practice_questions.csv`: 계산 결과와 해석을 연결하는 자가 점검 문제

외부 패키지 없이 표준 라이브러리만 사용한다. 복습 자료가 강의 노트의 숫자를
그대로 복사한 것이 아니라, 이 저장소의 연구 질문에 맞춘 합성 예제로 재현되도록
입력, 난수 seed, 경로 수를 모두 CSV와 코드에 명시한다.
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "sample" / "review_scenarios.csv"
OUTPUT_DIR = ROOT / "outputs" / "tables"


@dataclass(frozen=True)
class ReviewScenario:
    """복습용 몬테카를로 입력 가정.

    `base_value`는 현재 포트폴리오 가치를 뜻하며, 결과 해석의 기준 단위도
    동일하다. `annual_mu`와 `annual_sigma`는 연율 입력값이므로, 코드에서는
    `horizon_days / 252`로 환산한 투자기간에 맞춰 drift와 diffusion을 조정한다.
    """

    scenario_id: str
    base_value: float
    annual_mu: float
    annual_sigma: float
    horizon_days: int
    n_paths: int
    seed: int
    review_focus: str


def _read_scenarios(path: Path = INPUT_PATH) -> list[ReviewScenario]:
    """복습 시나리오 CSV를 구조화된 입력 객체 목록으로 변환한다.

    CSV는 사람이 수정하기 쉬운 형식이지만 모든 값이 문자열로 읽힌다. 계산 전에
    수치형 컬럼을 명시적으로 변환해, 단위가 섞이거나 빈 값이 들어왔을 때 어느
    단계에서 문제가 생겼는지 추적하기 쉽게 한다.
    """

    with path.open(newline="", encoding="utf-8") as fp:
        rows = csv.DictReader(fp)
        return [
            ReviewScenario(
                scenario_id=row["scenario_id"],
                base_value=float(row["base_value"]),
                annual_mu=float(row["annual_mu"]),
                annual_sigma=float(row["annual_sigma"]),
                horizon_days=int(row["horizon_days"]),
                n_paths=int(row["n_paths"]),
                seed=int(row["seed"]),
                review_focus=row["review_focus"],
            )
            for row in rows
        ]


def _mean(values: list[float]) -> float:
    """표본 평균을 계산한다."""

    return sum(values) / len(values)


def _sample_sd(values: list[float]) -> float:
    """표본 표준편차를 계산한다.

    경로 평균의 표준오차를 만들 때 표본분산의 관례인 n-1 분모를 사용한다.
    복습 관점에서는 "경로 수를 늘리면 평균 추정의 불확실성이 줄어든다"는 점을
    확인하는 용도이므로, 표준오차와 신뢰구간 폭을 함께 기록한다.
    """

    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _quantile(values: list[float], pct: float) -> float:
    """선형보간 분위수를 계산한다.

    몬테카를로 결과는 닫힌 형태의 정답 하나가 아니라 표본분포다. 따라서 평균뿐
    아니라 5%, 50%, 95% 분위수처럼 하방/중앙/상방 구간을 함께 봐야 한다.
    """

    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * pct
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[int(position)]
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def _round(value: float, digits: int = 6) -> float:
    """CSV에서 읽기 쉬운 자릿수로 숫자를 정리한다."""

    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(value, digits)


def _terminal_values(scenario: ReviewScenario, n_paths: int | None = None) -> list[float]:
    """GBM 해석해를 이용해 만기 포트폴리오 가치 표본을 생성한다.

    가정하는 모형은

    S_T = S_0 exp((mu - 0.5 sigma^2)T + sigma sqrt(T) Z)

    이다. 여기서 `Z`는 표준정규 난수다. 같은 seed를 고정하면 경로 수를 바꿔도
    앞부분 난수열이 재사용되므로, 수렴성 점검표에서 경로 수 증가의 효과를
    일관된 조건으로 비교할 수 있다.
    """

    rng = random.Random(scenario.seed)
    horizon = scenario.horizon_days / 252.0
    path_count = n_paths or scenario.n_paths
    drift = (scenario.annual_mu - 0.5 * scenario.annual_sigma**2) * horizon
    diffusion_scale = scenario.annual_sigma * math.sqrt(horizon)
    return [
        scenario.base_value * math.exp(drift + diffusion_scale * rng.gauss(0.0, 1.0))
        for _ in range(path_count)
    ]


def _distribution_note(scenario: ReviewScenario, loss_probability: float, p05: float, p95: float) -> str:
    """분포 요약표에 붙일 짧은 해석 메모를 만든다."""

    spread = p95 - p05
    if scenario.annual_sigma >= 0.30:
        return f"변동성 충격 구간: 5%-95% 폭 {spread:.2f}, 손실확률 {loss_probability:.1%}"
    if scenario.annual_sigma <= 0.12:
        return f"저변동성 구간: 손실확률 {loss_probability:.1%}, 하방 분위수 방어 여부 확인"
    return f"기준 구간: 평균과 하방 분위수의 차이를 손실확률과 함께 해석"


def build_distribution_summary(scenarios: list[ReviewScenario]) -> list[dict[str, object]]:
    """시나리오별 terminal value 분포를 복습용 지표로 요약한다."""

    output: list[dict[str, object]] = []
    for scenario in scenarios:
        values = _terminal_values(scenario)
        p05 = _quantile(values, 0.05)
        p25 = _quantile(values, 0.25)
        p50 = _quantile(values, 0.50)
        p75 = _quantile(values, 0.75)
        p95 = _quantile(values, 0.95)
        loss_probability = sum(value < scenario.base_value for value in values) / scenario.n_paths
        output.append(
            {
                "scenario_id": scenario.scenario_id,
                "review_focus": scenario.review_focus,
                "base_value": _round(scenario.base_value),
                "annual_mu": _round(scenario.annual_mu),
                "annual_sigma": _round(scenario.annual_sigma),
                "horizon_days": scenario.horizon_days,
                "n_paths": scenario.n_paths,
                "seed": scenario.seed,
                "mean_terminal_value": _round(_mean(values)),
                "p05_terminal_value": _round(p05),
                "p25_terminal_value": _round(p25),
                "p50_terminal_value": _round(p50),
                "p75_terminal_value": _round(p75),
                "p95_terminal_value": _round(p95),
                "terminal_iqr": _round(p75 - p25),
                "loss_probability": _round(loss_probability),
                "upside_20pct_probability": _round(
                    sum(value >= scenario.base_value * 1.20 for value in values) / scenario.n_paths
                ),
                "review_note": _distribution_note(scenario, loss_probability, p05, p95),
            }
        )
    return output


def build_convergence_check(scenarios: list[ReviewScenario]) -> list[dict[str, object]]:
    """경로 수가 늘어날 때 추정치가 안정되는지 확인하는 표를 만든다.

    몬테카를로는 난수 표본으로 기대값을 근사하므로, 경로 수가 너무 작으면 결과가
    seed에 과하게 의존한다. 이 표는 동일 seed에서 경로 수를 늘리며 평균, 하방
    분위수, 손실확률이 어느 정도 흔들리는지 복습하게 해준다.
    """

    output: list[dict[str, object]] = []
    for scenario in scenarios:
        checkpoints = [250, 500, 1000, 2000, scenario.n_paths]
        seen: set[int] = set()
        for n_paths in checkpoints:
            if n_paths in seen:
                continue
            seen.add(n_paths)
            values = _terminal_values(scenario, n_paths=n_paths)
            avg = _mean(values)
            sd = _sample_sd(values)
            standard_error = sd / math.sqrt(n_paths)
            ci95_half_width = 1.96 * standard_error
            output.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "review_focus": scenario.review_focus,
                    "n_paths": n_paths,
                    "seed": scenario.seed,
                    "mean_terminal_value": _round(avg),
                    "standard_error_mean": _round(standard_error),
                    "ci95_half_width": _round(ci95_half_width),
                    "ci95_half_width_pct_of_mean": _round(ci95_half_width / avg if avg else 0.0),
                    "p05_terminal_value": _round(_quantile(values, 0.05)),
                    "loss_probability": _round(sum(value < scenario.base_value for value in values) / n_paths),
                }
            )
    return output


def build_flashcards() -> list[dict[str, object]]:
    """개념 복습용 질문/답 카드를 만든다."""

    cards = [
        (
            "MC-01",
            "몬테카를로 시뮬레이션",
            "금융공학에서 몬테카를로 시뮬레이션을 쓰는 이유는?",
            "미래 가격이나 포트폴리오 가치가 하나의 값이 아니라 확률분포로 움직인다고 보고, 난수 경로를 반복 생성해 평균, 분위수, 손실확률 같은 분포 지표를 추정하기 위해서다.",
            "결론을 기대수익률 하나로 쓰지 말고 분포 지표와 함께 적었는지 확인한다.",
        ),
        (
            "MC-02",
            "GBM",
            "로그정규 terminal value 모형에서 `mu - 0.5 sigma^2` 항이 들어가는 이유는?",
            "가격이 로그수익률로 누적될 때 변동성의 볼록성 조정이 필요하기 때문이다. 이 항을 쓰면 산술 기대값이 mu와 일관되도록 지수변환 전 drift를 보정한다.",
            "수익률을 단순정규로 더한 것인지, 가격을 로그정규로 생성한 것인지 구분한다.",
        ),
        (
            "MC-03",
            "난수 seed",
            "seed를 기록해야 하는 이유는?",
            "같은 입력 가정에서 같은 난수열을 재생성해 결과표를 검산하고, 코드 변경 전후 차이가 모형 변화인지 난수 차이인지 분리하기 위해서다.",
            "`seed`, `n_paths`, `horizon_days`가 입력 또는 문서에 남아 있는지 본다.",
        ),
        (
            "MC-04",
            "경로 수",
            "경로 수를 늘리면 무엇이 개선되고 무엇은 그대로인가?",
            "표본 평균의 Monte Carlo 오차는 줄어들지만, 잘못 둔 평균/변동성 가정 자체가 자동으로 고쳐지지는 않는다.",
            "수렴성 점검은 표본오차 점검이지 모형 타당성 검증의 전부가 아니다.",
        ),
        (
            "MC-05",
            "분위수",
            "평균 terminal value보다 5% 분위수가 중요한 상황은?",
            "자본손실, VaR, 스트레스 하방 위험처럼 꼬리 손실이 의사결정의 핵심일 때다. 평균이 좋아도 하방 분위수가 나쁘면 위험 예산을 초과할 수 있다.",
            "평균, 중앙값, 5% 분위수, 손실확률을 같이 비교한다.",
        ),
        (
            "MC-06",
            "손실확률",
            "`loss_probability`의 기준점은 무엇인가?",
            "현재 포트폴리오 가치인 `base_value`보다 만기 가치가 낮게 끝난 경로의 비율이다.",
            "손실 기준이 원금, 무위험 수익률, 벤치마크 중 무엇인지 명확히 적는다.",
        ),
        (
            "MC-07",
            "변동성 민감도",
            "평균이 같고 변동성만 커지면 분포는 어떻게 바뀌는가?",
            "상방과 하방 꼬리가 동시에 두꺼워지고, 중앙값과 평균의 차이가 커질 수 있으며, 손실확률과 극단 분위수가 더 민감해진다.",
            "p05-p95 폭과 IQR을 함께 확인한다.",
        ),
        (
            "MC-08",
            "시간 환산",
            "`horizon_days / 252`를 쓰는 이유는?",
            "입력 평균과 변동성이 연율이므로 거래일 기준 투자기간을 연 단위 시간 T로 바꿔 drift와 diffusion을 같은 단위로 맞추기 위해서다.",
            "연율, 월율, 일율 입력을 섞지 않았는지 확인한다.",
        ),
        (
            "MC-09",
            "룩어헤드 바이어스",
            "시뮬레이션 입력 평균과 변동성을 실제 데이터에서 추정할 때 주의할 점은?",
            "평가 시점 이후 데이터를 입력 추정에 사용하면 미래 정보를 미리 본 것이므로, 추정 기간과 평가 기간을 시간 순서대로 분리해야 한다.",
            "샘플 기간, 추정 창, 리밸런싱 시점을 문서에 남긴다.",
        ),
        (
            "MC-10",
            "해석 한계",
            "합성 입력 기반 결과를 투자 결론처럼 말하면 안 되는 이유는?",
            "합성 가정은 계산 구조를 검증하기 위한 예시이며, 실제 시장의 구조 변화, 거래비용, 유동성, 세금, 모수 불확실성을 충분히 반영하지 못하기 때문이다.",
            "결과표 옆에 입력 가정과 한계를 같이 적는다.",
        ),
    ]
    return [
        {
            "card_id": card_id,
            "concept": concept,
            "question": question,
            "answer": answer,
            "verification_point": verification_point,
        }
        for card_id, concept, question, answer, verification_point in cards
    ]


def build_practice_questions() -> list[dict[str, object]]:
    """복습자가 결과표를 읽고 직접 답을 점검할 수 있는 문제를 만든다."""

    questions = [
        (
            "Q01",
            "수식",
            "GBM terminal value 공식에서 `sigma sqrt(T) Z`가 의미하는 확률적 충격을 설명하라.",
            "연율 변동성 sigma를 투자기간 T에 맞게 조정한 표준편차에 표준정규 난수 Z를 곱한 항이다. 경로별 무작위 충격을 만들며, T가 길거나 sigma가 클수록 분포 폭이 커진다.",
            "확률충격의 단위 환산을 이해했는지 확인한다.",
        ),
        (
            "Q02",
            "입력 가정",
            "`annual_mu`가 높아졌는데도 특정 표본에서 p05가 낮아질 수 있는 이유를 설명하라.",
            "p05는 평균뿐 아니라 변동성, 경로 수, 난수 표본에 영향을 받는다. 기대수익률이 높아도 변동성이 크게 증가하면 하방 꼬리가 더 나빠질 수 있다.",
            "평균과 변동성을 분리해서 해석한다.",
        ),
        (
            "Q03",
            "수렴성",
            "`review_convergence_check.csv`에서 경로 수가 커질 때 `standard_error_mean`이 줄어드는지 확인하라.",
            "표준오차는 표본 표준편차를 경로 수의 제곱근으로 나눈 값이므로, 같은 시나리오 안에서는 대체로 경로 수가 늘수록 작아져야 한다.",
            "난수 시뮬레이션의 표본오차를 숫자로 점검한다.",
        ),
        (
            "Q04",
            "손실확률",
            "`loss_probability`와 p05 terminal value는 같은 정보를 주는가?",
            "둘 다 하방 위험을 보지만 같지는 않다. 손실확률은 기준값 아래로 끝난 경로 비율이고, p05는 하위 5% 지점의 손실 크기를 보여준다.",
            "손실 빈도와 손실 크기를 구분한다.",
        ),
        (
            "Q05",
            "민감도",
            "STRESS_VOL 유형 시나리오에서 평균보다 p05와 p95의 변화 폭에 더 집중해야 하는 이유는?",
            "스트레스 변동성은 분포의 꼬리를 크게 바꾼다. 평균은 크게 움직이지 않아 보여도 하방 분위수와 상방 분위수 폭이 넓어져 위험 예산과 자본배분 판단이 달라진다.",
            "변동성 충격은 평균보다 꼬리와 폭으로 읽는다.",
        ),
        (
            "Q06",
            "검증",
            "복습용 표를 다시 생성한 뒤 baseline 결과와 숫자가 다를 때 먼저 확인할 항목은?",
            "입력 파일, seed, 경로 수, horizon_days, 연율 단위, 코드 변경 여부를 먼저 확인한다. 난수 생성 방식이 다르면 같은 가정이어도 숫자가 달라질 수 있다.",
            "재현성 문제를 입력, 난수, 구현 순서로 좁힌다.",
        ),
        (
            "Q07",
            "한계",
            "이 저장소의 합성 시나리오 결과를 실제 포트폴리오 투자 의사결정에 바로 쓰면 안 되는 이유는?",
            "실제 수익률 추정, 상관구조, 거래비용, 세금, 유동성, 리밸런싱 규칙, 모수 불확실성이 반영되지 않았기 때문이다.",
            "계산 구조 검증과 투자 검증을 구분한다.",
        ),
        (
            "Q08",
            "확장",
            "다자산 포트폴리오로 확장할 때 단일자산 GBM에서 추가로 필요한 입력은?",
            "자산별 기대수익률과 변동성뿐 아니라 자산 간 상관 또는 공분산 행렬이 필요하다. 독립 난수만 쓰면 분산효과와 동시 하락 위험을 잘못 볼 수 있다.",
            "포트폴리오 리스크는 개별 변동성과 상관을 함께 본다.",
        ),
    ]
    return [
        {
            "question_id": question_id,
            "topic": topic,
            "prompt": prompt,
            "answer_key": answer_key,
            "why_it_matters": why_it_matters,
        }
        for question_id, topic, prompt, answer_key, why_it_matters in questions
    ]


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
    """딕셔너리 행 목록을 CSV로 저장한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as fp:
        # Git diff와 문서 리뷰에서 불필요한 CRLF 잡음이 생기지 않도록 산출물 줄끝을 LF로 고정한다.
        writer = csv.DictWriter(fp, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate_review_materials() -> dict[str, int]:
    """복습 자료 CSV를 모두 생성하고 파일별 행 수를 반환한다."""

    scenarios = _read_scenarios()
    outputs = {
        "review_distribution_summary.csv": build_distribution_summary(scenarios),
        "review_convergence_check.csv": build_convergence_check(scenarios),
        "review_flashcards.csv": build_flashcards(),
        "review_practice_questions.csv": build_practice_questions(),
    }
    for filename, rows in outputs.items():
        _write_csv(rows, OUTPUT_DIR / filename)
    return {filename: len(rows) for filename, rows in outputs.items()}


def main() -> None:
    """명령행 실행 시 복습 자료를 모두 재생성한다."""

    counts = generate_review_materials()
    for filename, row_count in counts.items():
        print(f"wrote {row_count} rows to {OUTPUT_DIR / filename}")


if __name__ == "__main__":
    main()

# WR-201B Report — Funding Risk Evaluator

## Scope

Added one isolated deterministic funding-risk evaluator using caller-supplied
policy only.

## Implementation

- Added immutable, hashable `FundingRiskInput`.
- Added immutable, hashable `FundingRiskPolicy`.
- Added stateless `FundingRiskEvaluator`.
- Returned the shared WR-201A `RiskComponent`.
- Preserved funding sign exclusively through the reason code.
- Added no hidden or default production thresholds.

## Evaluation contract

Annualized funding magnitude:

```text
abs(funding_rate) * (24 / funding_interval_hours) * 365 * 100
```

Score:

```text
min(100, annualized_percent / extreme_annualized_percent * 100)
```

Risk levels are selected at the exact caller-supplied score boundaries.

## Excluded scope

- Open Interest and other risk factors.
- Risk aggregation or `RiskScore` population.
- Directional prediction.
- Intelligence or Decision integration.
- Exchange adapters, live data, persistence, APIs, CLI, alerts, AI, or
  trading.

## Tests

Focused tests cover exact fields, immutability, hashing, timestamp
normalization, all specified numeric validation, annualization, symmetric
positive/negative scoring, reason codes, score capping, exact level
boundaries, deterministic evaluation, contract compatibility, import
isolation, and Python 3.9 type hints.

## Verification

- Python 3.9.6 `py_compile`: passed.
- Focused WR-201B tests: 60 passed.
- Complete `tests/risk` suite: 78 passed.
- Deterministic project regression excluding four pre-existing live Telegram
  scripts: 1519 passed, 1 unrelated `urllib3` LibreSSL warning.
- `git diff --check`: passed.

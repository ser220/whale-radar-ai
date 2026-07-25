# WR-201E Report — Liquidation Risk Evaluator

## A. Branch

`wr-201e-liquidation-risk-evaluator`

## B. Files changed

- `app/risk/liquidations/__init__.py`
- `app/risk/liquidations/evaluator.py`
- `tests/risk/liquidations/test_liquidation_risk.py`
- `docs/reviews/WR-201E-liquidation-risk-evaluator.md`
- `docs/reports/WR-201E_REPORT.md`

## C. Exact implemented contract

- Frozen, hashable `LiquidationRiskInput` with exactly six requested fields.
- Frozen, hashable `LiquidationRiskPolicy` with exactly five requested fields
  and no defaults.
- Stateless `LiquidationRiskEvaluator` returning the shared `RiskComponent`.
- Local `app.risk.liquidations` exports only the three WR-201E contracts.

## D. Evaluation formula

```text
total_liquidation_notional =
    long_liquidation_notional + short_liquidation_notional

liquidation_percent =
    total_liquidation_notional / total_traded_notional * 100

score =
    min(
        100,
        liquidation_percent / extreme_liquidation_percent * 100,
    )

difference_percent =
    0 if total_liquidation_notional == 0
    else abs(long - short) / total_liquidation_notional * 100
```

Exact score boundaries map upward. The exact balanced difference boundary maps
to `LIQUIDATIONS_BALANCED`. Dominance changes only the reason code.

## E. Tests added

Focused pytest coverage includes exact schemas, frozen value semantics,
hashing, deterministic equality, text and numeric validation, liquidation
notional invariants, positive-zero normalization, datetime and UTC behavior,
policy bounds, formulas, dominance symmetry and reason codes, exact balanced
boundary behavior, score capping, exact level boundaries, return contract,
statelessness, isolation, unchanged existing contracts/evaluators and package
exports, documentation boundaries, and Python 3.9 type hints.

## F. Verification results

- Python 3.9.6 `py_compile`: passed.
- Focused WR-201E tests: 104 passed.
- Complete `tests/risk` suite: 345 passed.
- Deterministic regression with the same four WR-201D exclusions:
  1786 passed, 1 unrelated `urllib3` LibreSSL warning.
- `git diff --check`: passed.

## G. Git status

- The five requested WR-201E files are untracked.
- No existing file is modified.
- No commit or push performed.

## H. Deviations

None.

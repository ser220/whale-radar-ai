# WR-201D Report — CVD Risk Evaluator

## A. Branch

`wr-201d-cvd-risk-evaluator`

## B. Files changed

- `app/risk/flow/__init__.py`
- `app/risk/flow/cvd.py`
- `tests/risk/flow/test_cvd_risk.py`
- `docs/reviews/WR-201D-cvd-risk-evaluator.md`
- `docs/reports/WR-201D_REPORT.md`

## C. Exact implemented contract

- Frozen, hashable `CVDRiskInput` with exactly the five requested fields.
- Frozen, hashable `CVDRiskPolicy` with exactly the four requested fields and
  no defaults.
- Stateless `CVDRiskEvaluator` returning the shared `RiskComponent`.
- Local `app.risk.flow` exports only the three WR-201D contracts.

## D. Evaluation formula

```text
imbalance_percent = cvd_delta / total_volume * 100

score =
    min(
        100,
        abs(imbalance_percent)
        / extreme_imbalance_percent
        * 100,
    )
```

Exact score thresholds map upward. Imbalance sign affects only
`CVD_BUY_DOMINANT`, `CVD_SELL_DOMINANT`, or `CVD_BALANCED`.

## E. Tests added

Focused pytest coverage includes exact schemas, frozen value semantics,
hashing, deterministic equality, trimming and text validation, every requested
numeric validation, CVD/volume invariants, datetime and UTC behavior, policy
boundaries, formulas, sign symmetry, positive and negative zero, reason codes,
score capping, exact level boundaries, return contract, statelessness,
isolation, unchanged risk contracts and derivative evaluators, minimal
exports, and Python 3.9 type hints.

## F. Verification results

- Python 3.9.6 `py_compile`: passed.
- Focused WR-201D tests: 84 passed.
- Complete `tests/risk` suite: 241 passed.
- Deterministic regression with the same four WR-201C exclusions:
  1682 passed, 1 unrelated `urllib3` LibreSSL warning.
- `git diff --check`: passed.

## G. Git status

- The five requested WR-201D files are untracked.
- No existing file is modified.
- No commit or push performed.

## H. Deviations

None.

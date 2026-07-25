# WR-201C Report — Open Interest Risk Evaluator

## Branch

`wr-201c-open-interest-risk-evaluator`

## Files changed

- `app/risk/derivatives/__init__.py`
- `app/risk/derivatives/open_interest.py`
- `tests/risk/derivatives/test_open_interest_risk.py`
- `docs/reviews/WR-201C-open-interest-risk-evaluator.md`
- `docs/reports/WR-201C_REPORT.md`

## Exact implemented contract

- Frozen, hashable `OpenInterestRiskInput` with exactly the five requested
  fields.
- Frozen, hashable `OpenInterestRiskPolicy` with exactly the four requested
  fields and no defaults.
- Stateless `OpenInterestRiskEvaluator` returning the shared
  `RiskComponent`.
- Minimal derivative-package exports preserving all WR-201B funding exports.

## Formula

```text
change_percent =
    (open_interest - previous_open_interest)
    / previous_open_interest
    * 100

score =
    min(
        100,
        abs(change_percent)
        / extreme_change_percent
        * 100,
    )
```

Score thresholds map exact boundaries upward. OI sign affects only
`OI_INCREASE`, `OI_DECREASE`, or `OI_UNCHANGED`.

## Tests added

Focused pytest coverage includes exact schemas, frozen value semantics,
hashing, deterministic equality, text validation and trimming, all requested
numeric validation, OI value boundaries, datetime validation and UTC
normalization, policy boundaries, exact formulas, sign symmetry, reason codes,
score capping, exact upward level boundaries, return contract, determinism,
statelessness, isolation, unchanged `RiskScore`, WR-201B compatibility, and
Python 3.9 type hints.

## Verification results

- Python 3.9.6 `py_compile`: passed.
- Focused WR-201C tests: 79 passed.
- Complete `tests/risk` suite: 157 passed.
- Deterministic regression with the same four WR-201B exclusions:
  1598 passed, 1 unrelated `urllib3` LibreSSL warning.
- `git diff --check`: passed.

## Git status

- Modified: `app/risk/derivatives/__init__.py`.
- Untracked: the four requested new implementation, test, review, and report
  files.
- No commit or push performed.

## Deviations

None.

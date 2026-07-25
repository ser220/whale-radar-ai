# WR-201A Report — Risk Component Contract

## Scope

Added one shared immutable return contract for future risk evaluators.

## Implementation

- Added `RiskFactor` with eight stable uppercase string values.
- Added frozen, hashable `RiskComponent`.
- Exported the two new contracts from `app.risk`.
- Required `reason_code` to be a string without normalizing or interpreting it.
- Preserved every supplied score, level, factor, and reason-code value.

## Excluded scope

- Evaluators and calculations.
- Score ranges, normalization, clamping, and thresholds.
- Automatic score-to-level derivation.
- Score/level relationship validation.
- Aggregation and modification of `RiskScore`.
- Reason-code taxonomy and metadata payloads.
- Intelligence or Decision integration.

## Tests

Focused coverage verifies:

- valid construction, equality, immutability, and hashing;
- exact `RiskFactor` membership, values, and string reconstruction;
- exact preservation of supplied values;
- deterministic repeated construction;
- string-only `reason_code` without formatting policy;
- unchanged `RiskScore` and `RiskLevel` contracts;
- minimal public exports;
- isolation from Intelligence and Decision;
- Python 3.9-compatible public type hints.

## Verification

- Python 3.9.6 `py_compile`: passed.
- Focused WR-201A tests: 13 passed.
- Complete `tests/risk` suite: 18 passed.
- Deterministic project regression excluding four pre-existing live Telegram
  scripts: 1459 passed, 1 unrelated `urllib3` LibreSSL warning.
- The unfiltered regression was also attempted and stopped during collection
  because the four pre-existing scripts perform live Telegram network calls
  that the restricted environment rejected. No WR-201A test failed.
- `git diff --check`: passed.

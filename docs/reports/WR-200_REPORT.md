# WR-200 Report — Risk Score Foundation

## Scope

Added the standalone domain foundation for a common risk contract.

## Implementation

- Added immutable, hashable `RiskScore`.
- Added `RiskLevel` with `LOW`, `MEDIUM`, `HIGH`, and `EXTREME`.
- Exported both contracts from the isolated `app.risk` package.
- Added no calculation, threshold, service, persistence, or integration logic.

## Tests

Focused coverage verifies:

- valid score construction;
- value equality;
- frozen immutability;
- hashing;
- deterministic `RiskLevel` value mapping.

## Isolation

No existing Intelligence, Decision, Backtest, service, or runtime production
file was modified.

## Verification

- Python 3.9 `py_compile`: passed.
- Focused WR-200 tests: 5 passed.
- Deterministic project regression: 1446 passed, 1 unrelated
  `urllib3` LibreSSL warning.
- `git diff --check`: passed.

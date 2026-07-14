# PS-1 Shadow Intelligence Preview Report

## Status

Implemented on `ps-1-shadow-preview`; pending Architecture Review. No deployment
or Hostinger change is included.

## Objective

Add an opt-in, read-only Shadow Intelligence section to the existing Telegram
`/analyze` presentation without changing current decisions, recommendations,
Trade Readiness, confidence, signals or execution behavior.

## Implementation boundary

The existing `AnalyzeService` result remains unchanged. The production Decision
Engine and Trade Readiness Engine run exactly as before. After that result is
complete, `format_analyze_result()` may append one presentation-only section
when the feature flag is explicitly enabled.

The formatter reads an optional presentation payload at:

```python
result["shadow_intelligence"] = {
    "opinions": {
        "legacy_intelligence": {
            "direction": "BULLISH | BEARISH | NEUTRAL",
            "confidence": 0_to_100,
        },
        "trend_expert": {
            "direction": "BULLISH | BEARISH | NEUTRAL",
            "confidence": 0_to_100,
        },
    },
    "agreement": "HIGH | MEDIUM | LOW",
}
```

PS-1 does not create that payload or call ShadowIntelligenceEngine. If the flag
is enabled but no payload is available, Telegram displays `Shadow Intelligence
— Unavailable`. This is intentionally honest and keeps collection/orchestration
outside the formatter.

## Telegram preview

The dedicated `format_shadow_intelligence()` function shows only:

- fixed Legacy Expert and Trend Expert labels when their payloads exist;
- whitelisted `BULLISH`, `BEARISH`, or `NEUTRAL` direction;
- validated 0–100 confidence;
- whitelisted High, Medium, or Low agreement;
- fixed `Shadow Status: Experimental`.

Unknown direction, invalid confidence and unsupported agreement values become
`Unavailable`. Recommendation, action, BUY, SELL, TP, SL and all other payload
fields are ignored and cannot be rendered by the shadow formatter.

## Feature flag

Environment variable:

```text
SHADOW_INTELLIGENCE_PREVIEW_ENABLED
```

The default is disabled. Explicit true values are `1`, `true`, `yes`, `on`, and
`enabled` (case-insensitive). The Telegram handler passes the resulting boolean
to the formatter. With the flag disabled, `format_analyze_result()` takes its
existing path and produces byte-for-byte identical output.

No `.env` file or environment value is added or changed by PS-1.

## Files created

- `test_shadow_preview_formatter.py`;
- `docs/reports/PS-1_REPORT.md`.

## Files modified

- `app/telegram/analyze_formatter.py` — additive dedicated shadow formatter and
  optional append path;
- `app/telegram/polling_bot.py` — read-only feature flag and formatter argument.

## Safety

- Production decision logic changed: **NO**
- Recommendation formatting changed: **NO** when disabled; shadow formatter
  never renders recommendation fields
- Decision Engine changed: **NO**
- Trade Readiness changed: **NO**
- Confidence override: **NO**
- Existing result mutated: **NO**
- Trading signal created: **NO**
- Execution advice/logic created: **NO**
- Telegram formatting only: **YES**
- Hostinger changed/deployed: **NO**
- Dependency added: **NO**

## Verification

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/telegram/analyze_formatter.py \
  app/telegram/polling_bot.py \
  test_shadow_preview_formatter.py

./venv/bin/python -m unittest -v test_shadow_preview_formatter.py
./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_legacy_adapter.py
./venv/bin/python -m unittest -v test_trend_adapter.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
```

Also inspect the complete branch diff, unrelated untracked files,
`git diff --check`, and confirm that no decision, readiness, service, database,
dependency or deployment file is changed.

Results:

- Python 3.9 compile check: passed;
- `test_shadow_preview_formatter.py`: 9 tests passed;
- `test_shadow_intelligence.py`: 10 tests passed;
- `test_legacy_adapter.py`: 11 tests passed;
- `test_trend_adapter.py`: 10 tests passed;
- `test_market_state_engine.py`: 30 tests passed;
- `test_core.py`, `test_filter.py`, `test_parser.py`: passed;
- disabled-path diff inspection: existing formatter body unchanged; only the
  final optional append boundary is additive;
- no live Telegram, network, database or provider test was run.

## Architecture deviations

No Shadow payload producer is added because the task restricts the change to
read-only Telegram formatting and forbids production logic changes. The UI
contract is ready for a separately reviewed producer; until then the enabled
preview correctly reports unavailable data.

## Open questions

1. Which separately reviewed read-only boundary will create the presentation
   payload from actual ShadowIntelligenceEngine output?
2. Should agreement be supplied directly by shadow orchestration or mapped from
   a future explicit consensus metric?
3. Should preview availability and formatter validation failures receive
   non-sensitive telemetry before enabling the flag in any environment?

No merge, deployment, Hostinger change or subsequent production sprint is
authorized by PS-1.

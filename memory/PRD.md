# Fractal Module PRD

## Original Problem Statement
Клонировать репозиторий, развернуть фронт, бэк и админку. Работать только с модулем Fractal.
Реализовать задачи U3, U4, U5, U6.

## Implemented Features

### U3 — Multi-Horizon (DONE - 2026-02-22)
- Backend returns different matches for different horizons (7d=30, 30d=20, 365d=10)
- `horizon` field added to meta response
- DataStatusIndicator shows DATA: REAL/FALLBACK with reasons

### U4 — Hybrid Chart (DONE - 2026-02-22)
- HybridSummaryPanel shows both % returns AND price targets
- ForecastTooltip for hover in forecast zone shows prices/dates/returns
- Price formatting with K/M suffix

### U5 — Signal Header (DONE - 2026-02-22)
- 4 human-friendly cards: Signal, Confidence, Market Mode, Risk
- Advanced metrics toggle with raw scores
- Tooltips explaining each metric

### U6 — Scenarios 2.0 (DONE - 2026-02-22)
- ScenarioBox component with Bear/Base/Bull cards
- Target prices calculated: basePrice * (1 + return)
- RangeStrip showing P10-P90 visual range
- OutcomeStats: probUp, avgMaxDD, tailRiskP95, sampleSize
- DATA: REAL/FALLBACK indicator
- Different targets for different horizons:
  - 7d: P10=$61K, P50=$68K, P90=$74K
  - 365d: P10=$25K, P50=$110K, P90=$595K

## Architecture

### Backend (Node.js/Fastify)
- `/app/backend/src/modules/fractal/focus/focus-pack.builder.ts`
  - buildFocusPack() - main function
  - buildScenarioPack() - U6: scenarios calculation
  - buildDivergenceFromUnified() - divergence metrics
- `/app/backend/src/modules/fractal/focus/focus.types.ts`
  - ScenarioPack interface
  - ScenarioCase type

### Frontend (React)
- `/app/frontend/src/pages/FractalPage.js` - Main page
- `/app/frontend/src/components/fractal/`
  - `ScenarioBox.jsx` - U6: Bear/Base/Bull scenarios
  - `SignalHeader.jsx` - U5: 4 signal cards
  - `DataStatusIndicator.jsx` - U3: REAL/FALLBACK
  - `chart/FractalChartCanvas.jsx` - U4: ForecastTooltip
  - `chart/FractalHybridChart.jsx` - U4: Price targets

### API
- `GET /api/fractal/v2.1/focus-pack?symbol=BTC&focus={horizon}`
  - Returns: meta, overlay, forecast, diagnostics, scenario

## Testing Status (2026-02-22)
- Backend: 95% - All APIs working, minor phaseSnapshot issue
- Frontend: 100% - All components rendering correctly
- Integration: 100% - Full flow working

## Acceptance Criteria Status

### U3 ✅
- [x] 7d and 365d return different matches/replay/synthetic
- [x] DATA: REAL/FALLBACK with reason displayed

### U4 ✅
- [x] Hybrid shows 2 lines with hover giving 2 prices
- [x] Forecast zone has price-levels not just shapes

### U5 ✅
- [x] Header readable without context (Signal/Confidence/Mode/Risk)

### U6 ✅
- [x] 7d and 365d give different target prices
- [x] Preset changes scenarios (via horizon change)
- [x] Hover and ScenarioBox show consistent prices
- [x] DATA: REAL/FALLBACK displayed with sampleSize

## Next Action Items
1. U7 — Risk Box 2.0: sizing explanation, Crisis mode reasoning
2. Add phaseSnapshot to terminal endpoint for Market Mode card
3. Simple/Pro mode toggle for user preference

## P0/P1/P2 Features Remaining

### P0 (Critical)
- None - All U3-U6 implemented

### P1 (Important)
- U7 Risk Box 2.0
- phaseSnapshot in terminal endpoint
- Preset selector (Conservative/Balanced/Aggressive)

### P2 (Nice to have)
- Simple/Pro mode toggle
- Historical accuracy tracking
- SPX copy of BTC structure

## User Personas
- Institutional Traders - Need quick signal + scenario interpretation
- Retail Traders - Need simplified view with Bear/Base/Bull scenarios
- Researchers - Need advanced metrics access

## Technical Debt
- Preview server requires wake up activation (known platform issue)

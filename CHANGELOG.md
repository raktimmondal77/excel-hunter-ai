# CHANGELOG — EXCEL HUNTER AI

## Stage 3 (this version) — Precision Discovery & Honest Scoring

### Fixed
- **App-crashing import bug**: `src/fiverr_manager.py` used `Tuple` in a type
  annotation without importing it (`NameError` on Python < 3.14 — the module,
  the whole dashboard and the test suite failed to start).
- **`requests` missing from requirements.txt** even though every discovery
  adapter imports it (it only worked because Streamlit installs it as an
  indirect dependency).
- Scan success message vanished instantly in the UI (`st.rerun()` wiped it) —
  the scan report now persists in session state with a per-source breakdown.
- Remotive salary strings like "$60k" were parsed as ₹60 (missing the k
  suffix) — annual salaries are now recorded as context, never as gig budgets.
- Application tracker recorded the bid in the job's original currency while
  the repository stores INR — now always records ₹.
- Redundant/contradictory WHERE clauses in `delete_sample_data()` cleaned up.
- `add_col_if_missing` migration ordering issue for the new
  `discovery_runs.irrelevant_skipped` column.

### Added
- **3 new zero-cost job sources**: RemoteOK, Jobicy and Working Nomads
  (WeWorkRemotely RSS was evaluated but is bot-blocked; excluded deliberately).
- **`src/currency.py`**: central FX table, `to_inr()`, currency aliases,
  money-text parser (`$60k` → ₹51,00,000), annual-salary heuristic.
- **Strict Excel relevance gate** (`is_excel_job`): distinguishes real
  spreadsheet work from "excel" used as an English verb and from fuzzy
  API matches. Enforced in every adapter AND double-checked in the engine.
- **Freshness-aware scoring**: postings decay with age; >20 days flagged;
  >30 days flagged as stale. Freelancer scan restricted to the last 7 days.
- **Currency-aware scoring**: a $400 budget is scored as ₹34,000, not ₹400.
- **Soft-warning vs severe-flag distinction**: rush deadline / tiny budget /
  stale posting are quality notes (−5); fraud signals stay severe (−25).
- **Per-source scan statistics**: found / imported / junk-filtered /
  duplicates / errors, shown in the UI and printed by the CLI runner.
- **Proposals embed pricing**: "Investment & Timeline" line with the
  recommended fixed quote and delivery estimate (from the pricing assistant;
  optional parameter, fully editable, never invented).
- **Home page "Top Jobs to Apply for Right Now"** panel.
- **Job list upgrades**: score badges, priority badges, category chips,
  posting age, sorting (best match / newest / highest budget / risky last),
  priority filter, keyword search, hide-risky toggle, 25-card paging.
- **26 new automated tests** (76 total): currency, relevance gate, scoring
  v3, new adapters (offline), proposal pricing, engine junk gate.
- `CHANGELOG.md`, expanded README with scoring table and source matrix.

### Changed
- Freelancer adapter: searches 4 high-signal queries (was: only the first
  search term), `from_time` + `sort=latest`, real client signals (escrow,
  featured, urgent, bid counts) instead of the blanket "Freelancer Client"
  credibility, budgets converted to INR at import with the original preserved.
- Remotive adapter: searches both "excel" and "spreadsheet".
- `run_discovery.py`: prints per-source statistics and the top 5 fresh
  opportunities from each scan.
- Evaluation engine restructured (see README scoring table); the public
  `evaluate_job()` signature is backward compatible.
- Engine default `max_per_source` raised to 20; new-job details returned to
  the caller for immediate display.

### Verification
- 76/76 tests green (`python -m pytest`).
- Live end-to-end scan verified against real APIs: 210 raw candidates
  evaluated → 207 non-Excel postings rejected → 3 genuine Excel jobs
  imported, INR-converted and honestly scored.
- Streamlit dashboard verified page-by-page in a real browser session
  (no exceptions in logs).

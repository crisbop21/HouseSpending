# Implementation Plan

Working plan for building the Couple Expense Tracker. Each phase has concrete tasks, dependencies, acceptance criteria, and rough effort estimates. Tasks are written so they can be turned into GitHub issues directly.

This plan pairs with `TECHNICAL_BRIEF.md`. Refer to the brief for architecture and data model details. This document is about sequencing and execution.

## How to Use This Document

1. Each phase has a milestone in GitHub
2. Each task becomes an issue with the title shown
3. Effort estimates use shirt sizes: XS (under 1 hour), S (1 to 3 hours), M (half day), L (full day), XL (multi day)
4. Tasks within a phase are mostly sequential unless marked parallel
5. Acceptance criteria at the bottom of each phase must all be true before moving on

## Pre Phase: Foundations

Before any phase work, get the scaffolding ready. This is one weekend of setup.

### Tasks

| # | Task | Effort | Notes |
|---|---|---|---|
| 0.1 | Create GitHub repo, add LICENSE, .gitignore (Python), and empty README | XS | Use the existing technical brief as starter content for README |
| 0.2 | Create Supabase project (free tier), record project URL and anon key | XS | Project name suggestion: expense tracker prod |
| 0.3 | Create Anthropic API key, set up a separate billing alert at SGD 10 | XS | Phase 1 will not use this but set up early |
| 0.4 | Set up local Python env with pyenv or uv, Python 3.11+ | S | Document the exact command in docs/deployment.md |
| 0.5 | Create requirements.txt with the Phase 1 minimum dependencies | XS | streamlit, supabase, pandas, plotly, python-dotenv, pydantic |
| 0.6 | Set up .env.example with all keys (no real values) and add real .env to .gitignore | XS | |
| 0.7 | Initial folder structure as defined in the brief, with __init__.py files and empty stubs | S | Even empty modules; commit this as the baseline |
| 0.8 | Add basic CI: GitHub Actions running pytest and ruff on push | S | Optional but cheap and prevents drift |
| 0.9 | Create Streamlit Cloud account, link to GitHub repo, deploy empty app | S | Confirms the deploy pipeline works before there is anything to deploy |

### Acceptance criteria

1. Empty Streamlit app shows "Hello world" both locally and on Streamlit Cloud
2. Supabase project is reachable from local Python session
3. Repo has clean structure with no committed secrets
4. Both users have access to the GitHub repo and the Streamlit Cloud deploy URL

---

## Phase 1: MVP

Goal: prove out the data model, manual entry workflow, and core dashboard. No LLM, no PDF upload yet. This phase has to feel complete enough that both users actually log expenses for one full month.

Estimated effort: 5 to 8 working days spread over 3 to 4 weeks part time.

### 1.A: Database schema

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.A.1 | Write `sql/001_init_schema.sql` with all tables from the brief | M | Pre Phase |
| 1.A.2 | Write `sql/002_seed_categories.sql` with 15 default categories and color hex values | S | 1.A.1 |
| 1.A.3 | Write `sql/003_audit_triggers.sql`: function plus triggers on transactions, budgets, goals, merchants | M | 1.A.1 |
| 1.A.4 | Write `sql/004_rls_policies.sql`: enable RLS, allow authenticated read and write all rows | S | 1.A.1 |
| 1.A.5 | Apply all SQL files in order via Supabase SQL editor, verify tables exist | XS | 1.A.1 to 1.A.4 |
| 1.A.6 | Create both user accounts in Supabase Auth, insert matching rows in `users` table | XS | 1.A.5 |
| 1.A.7 | Insert seed cards (5 to 6) for each user via SQL editor | XS | 1.A.6 |

### 1.B: Auth and app shell

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.B.1 | Implement `src/db.py`: Supabase client wrapper, singleton pattern, env based config | S | Pre Phase |
| 1.B.2 | Implement `src/auth.py`: login form, session state, logout | M | 1.B.1, 1.A.6 |
| 1.B.3 | Implement `streamlit_app.py`: gate everything behind auth, set up sidebar navigation | S | 1.B.2 |
| 1.B.4 | Apply mobile responsive CSS overrides via st.markdown with style block | M | 1.B.3 |
| 1.B.5 | Create `src/models.py` with Pydantic models for all tables (read and write variants) | M | 1.A.1 |

### 1.C: Quick Add page

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.C.1 | Build `pages/01_quick_add.py` form: date, amount, currency, card select, merchant text, category dropdown, split type radio | M | 1.B.5 |
| 1.C.2 | Implement merchant normalization in `src/categorization/normalizer.py` with unit tests | M | parallel with 1.C.1 |
| 1.C.3 | Wire form submit: normalize merchant, lookup or insert in `merchants`, insert transaction with audit | M | 1.C.1, 1.C.2 |
| 1.C.4 | Add "last used card" memory in session state for one tap reuse | XS | 1.C.3 |
| 1.C.5 | Add inline FX rate input when card currency is USD, compute amount_sgd | S | 1.C.3 |

### 1.D: Transactions page

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.D.1 | Build `pages/04_transactions.py` with a paginated table (st.data_editor) | M | 1.B.5 |
| 1.D.2 | Add filters: date range, card, category, split type, merchant search | M | 1.D.1 |
| 1.D.3 | Wire inline edits to update transactions and write audit log entries | M | 1.D.1 |
| 1.D.4 | Add bulk action buttons: change category for selection, change split type for selection, delete selection | M | 1.D.1 |
| 1.D.5 | Add CSV export button for current filter view | S | 1.D.1 |

### 1.E: Settings page (minimal)

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.E.1 | Build `pages/08_settings.py` with sections: Cards, Categories, Audit Log, Export | S | 1.B.5 |
| 1.E.2 | Cards section: list, add, edit nickname, mark inactive | S | 1.E.1 |
| 1.E.3 | Categories section: list, add, rename, set color, archive | S | 1.E.1 |
| 1.E.4 | Audit log viewer: filterable by table, user, date range, last 200 rows | M | 1.E.1, 1.A.3 |
| 1.E.5 | Joint share split percentage setting (default 50/50) stored in a `settings` table or as a row in a kv table | S | 1.E.1 |

### 1.F: Dashboard (basic)

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.F.1 | Build `streamlit_app.py` home view: top strip with this month, last month, YTD totals, three views each | M | 1.D wired |
| 1.F.2 | Add donut chart: spend by category, current month | S | 1.F.1 |
| 1.F.3 | Add stacked bar chart: monthly spend by category, last 12 months | M | 1.F.1 |
| 1.F.4 | Add recent transactions section (last 20, with edit link) | S | 1.F.1 |
| 1.F.5 | Mobile layout: collapse charts to single column, hide sidebar by default on mobile | M | 1.F.1 to 1.F.4 |

### 1.G: Phase 1 polish

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1.G.1 | End to end test: log 30 transactions across both users, verify all dashboard numbers reconcile manually | M | All Phase 1 |
| 1.G.2 | Write `docs/runbook.md`: how to back up Supabase, how to restore, how to invite a new user (in case wife joins from new device) | S | 1.A done |
| 1.G.3 | Update README with quick start: setup, first run, deploy | S | 1.A done |
| 1.G.4 | Tag v0.1.0 release | XS | All above |

### Phase 1 Acceptance Criteria

1. Both users can log in and add a transaction in under 30 seconds on mobile
2. Dashboard shows accurate month to date totals matching manual reconciliation
3. Audit log captures every change with diff
4. CSV export produces a clean file openable in Excel
5. Both users have logged at least one full month of real expenses (this is the validation gate, not a development task)

---

## Phase 2: LLM Extraction and Categorization

Goal: replace manual entry of statement transactions with vision based extraction. After this phase the monthly workflow is upload, review, confirm.

Estimated effort: 4 to 6 working days spread over 2 to 3 weeks part time. Cannot start until Phase 1 acceptance is met.

### 2.A: Extraction pipeline

| # | Task | Effort | Depends on |
|---|---|---|---|
| 2.A.1 | Implement `src/extraction/pdf_to_images.py`: convert PDF to PIL images at 200 DPI | S | Phase 1 |
| 2.A.2 | Write extraction prompt in `src/extraction/prompts.py` with strict JSON schema, redaction rules for PAN | M | parallel with 2.A.1 |
| 2.A.3 | Implement `src/extraction/claude_extractor.py`: page by page extraction, error handling, retry on JSON parse failure | M | 2.A.1, 2.A.2 |
| 2.A.4 | Add a `staging_transactions` table or use `transactions` with status column for pending review | S | Phase 1 schema |
| 2.A.5 | End to end test: feed 3 real statements (1 SGD bank, 1 USD bank, 1 with refunds), verify extraction quality, log accuracy | L | 2.A.3 |

### 2.B: Upload page

| # | Task | Effort | Depends on |
|---|---|---|---|
| 2.B.1 | Build `pages/02_upload.py`: file uploader, card selector, period picker, FX rate input for USD | M | 2.A.3 |
| 2.B.2 | Wire upload flow: store file in Supabase Storage, create `statements` row, run extraction async with progress indicator | L | 2.B.1, 2.A.3 |
| 2.B.3 | Handle multi page PDFs (loop through pages, merge results, dedupe) | M | 2.B.2 |
| 2.B.4 | Error handling: failed extraction marks statement status as `failed`, user can retry | S | 2.B.2 |

### 2.C: Review Queue

| # | Task | Effort | Depends on |
|---|---|---|---|
| 2.C.1 | Build `pages/03_review_queue.py`: table of pending transactions per statement | M | 2.A.4 |
| 2.C.2 | Inline edit on every field, with the extracted value pre filled and editable | M | 2.C.1 |
| 2.C.3 | Bulk actions: confirm all, mark all as joint, apply category to all matching merchant | S | 2.C.1 |
| 2.C.4 | Confirm action: move to `transactions`, update statement status, write audit | M | 2.C.1 |
| 2.C.5 | Discard action: delete from staging, log reason | S | 2.C.1 |

### 2.D: LLM Categorization

| # | Task | Effort | Depends on |
|---|---|---|---|
| 2.D.1 | Implement `src/categorization/llm_categorizer.py`: prompt with categories list, returns category id and confidence | M | Phase 1 |
| 2.D.2 | Implement `src/categorization/merchant_cache.py`: lookup, insert on miss, update times_seen and last_seen_at | M | 2.D.1 |
| 2.D.3 | Wire into transaction insert flow: cache lookup first, LLM fallback, store result | M | 2.D.2 |
| 2.D.4 | Add override flow: when user changes category, update `merchants.user_override_category_id` | S | 2.D.3 |
| 2.D.5 | Backfill: re categorize all Phase 1 transactions through the new pipeline (one off script) | M | 2.D.3 |

### 2.E: Cost monitoring

| # | Task | Effort | Depends on |
|---|---|---|---|
| 2.E.1 | Add token and cost logging to extraction_meta on statements | S | 2.A.3 |
| 2.E.2 | Add a small admin view in Settings showing cumulative API spend by month | S | 2.E.1 |

### Phase 2 Acceptance Criteria

1. A 30 transaction statement is extracted, reviewed, confirmed, and posted in under 5 minutes end to end
2. Extraction accuracy on real statements is above 90% for fields (date, amount, merchant, type)
3. Categorization hit rate from cache is above 50% by end of first month using Phase 2 (will grow over time)
4. Total monthly LLM spend is under SGD 5
5. PAN never appears in any logs or LLM payloads (verified by spot check of one extraction's full request payload)

---

## Phase 3: Budgets, Goals, Subscriptions, Polish

Goal: replace any external spreadsheet entirely. After this phase, this app is the single source of truth.

Estimated effort: 4 to 5 working days spread over 2 weeks part time.

### 3.A: Budgets

| # | Task | Effort | Depends on |
|---|---|---|---|
| 3.A.1 | Build `pages/06_budgets.py`: list budgets, add, edit, archive | M | Phase 1 schema |
| 3.A.2 | Add applies_to selector (couple, user A, user B) and period selector (monthly, annual) | S | 3.A.1 |
| 3.A.3 | Implement `src/budgets.py`: compute current period spend vs budget per category | M | 3.A.1 |
| 3.A.4 | Add budget progress module to dashboard | S | 3.A.3 |
| 3.A.5 | Add rollover indicator: show variance from previous month | S | 3.A.3 |

### 3.B: Goals

| # | Task | Effort | Depends on |
|---|---|---|---|
| 3.B.1 | Build `pages/07_goals.py`: list, add, edit, archive goals | M | Phase 1 schema |
| 3.B.2 | Implement `src/goals.py`: compute progress for linked category goals (sum of category spend) | S | 3.B.1 |
| 3.B.3 | Add manual progress update field for unlinked goals | S | 3.B.1 |
| 3.B.4 | Add goals progress module to dashboard | S | 3.B.2 |

### 3.C: Subscription detector

| # | Task | Effort | Depends on |
|---|---|---|---|
| 3.C.1 | Implement `src/subscriptions.py`: detector logic (3+ occurrences, 25 to 35 day cadence, 10% amount tolerance) | M | Phase 1 |
| 3.C.2 | Build `pages/05_subscriptions.py`: detected subscriptions table, monthly burn total, top 5 list | M | 3.C.1 |
| 3.C.3 | Add "mark as not subscription" toggle that sets `is_subscription_candidate=false` and excludes from future runs | S | 3.C.2 |
| 3.C.4 | Add subscription burn module to dashboard | S | 3.C.1 |

### 3.D: Excel Export

| # | Task | Effort | Depends on |
|---|---|---|---|
| 3.D.1 | Implement `src/export.py`: multi sheet xlsx with transactions, monthly summary, category summary, budget tracking | L | All Phase 3 features |
| 3.D.2 | Add date range picker and format selector to Settings export section | S | 3.D.1 |
| 3.D.3 | Format with proper number formats, headers, frozen rows, conditional formatting on budget variance | M | 3.D.1 |

### 3.E: Polish

| # | Task | Effort | Depends on |
|---|---|---|---|
| 3.E.1 | Mobile UX pass: test every page on phone, fix any cramped layouts | M | All Phase 3 |
| 3.E.2 | Loading states: skeleton or spinner on every async call | S | All Phase 3 |
| 3.E.3 | Empty states: friendly messages on empty tables instead of blank screens | S | All Phase 3 |
| 3.E.4 | Error states: friendly messages on API failures instead of stack traces | S | All Phase 3 |
| 3.E.5 | Tag v1.0.0 release | XS | All above |

### Phase 3 Acceptance Criteria

1. Both users have stopped using their previous spreadsheet
2. Subscription detector finds at least 80% of known recurring charges
3. Excel export reproduces the spreadsheet workflow at year end
4. Mobile experience does not require horizontal scroll on any page
5. App handles gracefully: empty data, slow API, failed extraction, expired session

---

## Phase 4: Nice to Have

No commitment, no schedule. Pick from the menu when something becomes annoying enough.

| # | Idea | Effort | When to consider |
|---|---|---|---|
| 4.1 | FX rate auto fetch from frankfurter.app | S | When manual FX entry feels tedious |
| 4.2 | Receipt photo attachment per transaction | M | When reconciliation requires receipts |
| 4.3 | Annual review report (Year in Review style PDF) | L | December of any year |
| 4.4 | Anomaly alerts (category spend up 50%+ MoM) | M | After 6+ months of data |
| 4.5 | Telegram bot for one tap entry | L | If Streamlit mobile entry friction stays high |
| 4.6 | Weekly email digest summary | M | If checking dashboard becomes a chore |
| 4.7 | Splitwise style settle up ledger | L | If joint share percentage drifts from 50/50 |
| 4.8 | Multi currency expansion (COP, etc) | M | If Latin America trips become regular |

---

## Risks Tracked Across Phases

These are not tasks but watchpoints during development. Review weekly during build.

| Risk | Trigger | Mitigation |
|---|---|---|
| Extraction accuracy below 90% | First real statement test | Add per bank prompt variants; consider fallback to OCR plus structured prompt |
| LLM costs exceed SGD 10 per month | Month 2 of Phase 2 | Audit cache hit rate; tighten merchant normalization to increase cache hits |
| Streamlit Cloud cold starts annoy daily use | Phase 1 acceptance | Move to small VPS (DigitalOcean SGD 6 per month or similar) |
| Wife disengages from the tool | Phase 1 month 2 | Reassess Quick Add UX; consider Telegram bot earlier |
| Schema needs migration mid build | Any phase | Use ordered SQL migration files, never edit in place |
| Supabase free tier limits hit | Year 2+ | Upgrade to Pro at USD 25 per month, or self host Postgres on VPS |

---

## Working Cadence Suggestion

Personal project, no rush, but momentum matters.

1. One coding session per week, 2 to 3 hours, ideally Sunday before football
2. One ship session every fortnight: deploy, test, get feedback from wife
3. Phase 1 must ship before Phase 2 starts. No partial migration. Avoids the half built tool death spiral
4. Keep a simple changelog in CHANGELOG.md, one line per change, dated
5. Use GitHub Projects or Issues to track this plan's tasks. Do not let the plan and the actual work drift apart

---

## Definition of Done (Per Task)

A task is done when:

1. Code is merged to main
2. The feature works on the deployed Streamlit Cloud app, not just locally
3. If applicable, a unit test exists in `tests/`
4. README or runbook updated if user facing or operational changes
5. The task issue is closed with a brief note on what was built

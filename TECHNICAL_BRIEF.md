# Couple Expense Tracker

Technical brief for a personal expense tracking application built for two users to manage shared and individual finances across multiple cards in SGD and USD.

## 1. Overview

A web application for a couple to track expenses from debit and credit card statements across 5 to 6 cards. The system supports manual entry and statement uploads, uses an LLM to extract transactions from PDF or image statements, categorizes spending through a learned merchant database, and presents both individual and couple level analytics.

The product is optimized for monthly workflows. At the end of each month one user uploads statements, the app extracts and categorizes transactions, the user reviews and confirms, and the dashboard updates with the latest spend, budget tracking, and subscription insights.

## 2. Goals and Non Goals

### Goals

1. Reduce monthly expense tracking time to under thirty minutes per month
2. Provide a single source of truth for couple level finances across all cards and currencies
3. Enable category level budgeting and savings goal tracking
4. Surface subscription and recurring spend automatically without manual setup
5. Allow flexible joint versus personal tagging on every transaction
6. Produce clean exports for tax season

### Non Goals

1. Real time bank account aggregation through Plaid, SaltEdge, or similar providers
2. Investment portfolio tracking (handled separately)
3. Bill payment or money movement features
4. Multi user beyond the couple, no advisor access, no accountant view
5. Mobile native apps (responsive web only)

## 3. Users

Two user accounts only. Both have full read and write access. There is no role hierarchy and no public sharing. Authentication is handled by Supabase Auth with email and password.

## 4. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Streamlit | Fast to build, good enough for two users, native Python integration |
| Backend logic | Python 3.11+ | Same language as Streamlit, simplifies deployment |
| Database | Supabase (Postgres) | Managed Postgres, built in auth, row level security, free tier covers this use case |
| Auth | Supabase Auth | Email and password, two seats only |
| File storage | Supabase Storage | For uploaded statements, encrypted at rest |
| LLM extraction | Anthropic Claude API (vision) | PDF page rasterization then image input for transaction extraction |
| LLM categorization | Anthropic Claude API (text) | New merchant categorization, with merchant cache to minimize calls |
| Hosting | Streamlit Community Cloud | Free, GitHub integration, sufficient for two user load |
| Secrets | Streamlit secrets and Supabase env vars | API keys never in repo |

### Key Python libraries

```
streamlit
supabase
pandas
plotly
pdf2image
pillow
anthropic
python-dotenv
pydantic
openpyxl
```

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  Pages: Login, Quick Add, Upload, Review Queue, Transactions│
│         Dashboard, Budgets, Goals, Subscriptions, Settings  │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
┌─────────────────────────┐      ┌──────────────────────────┐
│   Python Service Layer  │      │   Anthropic Claude API   │
│  - Statement processor  │◄────►│  - Vision extraction     │
│  - Categorization       │      │  - Categorization        │
│  - FX handling          │      └──────────────────────────┘
│  - Subscription detector│
│  - Budget calculator    │
│  - Audit logger         │
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                     Supabase (Postgres)                       │
│  Tables: users, cards, statements, transactions, merchants,  │
│          categories, budgets, goals, audit_log, fx_rates     │
│  Storage: raw statement files                                 │
│  Auth: email and password                                     │
└──────────────────────────────────────────────────────────────┘
```

### Statement processing flow

1. User uploads PDF or image of statement on Upload page
2. File is stored in Supabase Storage with metadata in `statements` table (status: pending)
3. PDF pages converted to images via `pdf2image` at 200 DPI
4. Each page sent to Claude API with structured extraction prompt and JSON schema
5. Extracted transactions written to a staging area with status `pending_review`
6. User opens Review Queue, edits or confirms each transaction
7. Confirmed transactions move to `transactions` table, statement status flips to `processed`
8. Categorization runs: merchant lookup first, LLM fallback for unknowns

### Categorization flow

```
new transaction
      │
      ▼
normalize merchant string (uppercase, strip noise, remove location codes)
      │
      ▼
lookup in `merchants` table by normalized_name
      │
      ├── hit: apply stored category (override takes precedence over default)
      │
      └── miss: call Claude API with merchant + transaction context
                store result in `merchants` table with confidence
                user can override on Review Queue or anywhere
                override updates `merchants` table for future
```

The merchant cache is the core efficiency lever. After two to three months of usage, most transactions hit the cache and the LLM is only called for genuinely new merchants.

## 6. Data Model

All monetary amounts stored as `numeric(14,2)`. All dates as `date` or `timestamptz`. All foreign keys with `on delete restrict` unless noted.

### `users`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK, mirrors Supabase auth.users.id |
| display_name | text | |
| created_at | timestamptz | |

### `cards`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| owner_user_id | uuid | FK users |
| nickname | text | "DBS Altitude", "Citi PremierMiles" |
| issuer | text | DBS, OCBC, Citi, etc |
| card_type | text | credit, debit |
| currency | text | SGD, USD |
| last_four | text | for matching during extraction |
| is_active | boolean | default true |

### `statements`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| card_id | uuid | FK cards |
| period_start | date | |
| period_end | date | |
| storage_path | text | Supabase Storage key |
| status | text | pending, extracting, pending_review, processed, failed |
| uploaded_by | uuid | FK users |
| uploaded_at | timestamptz | |
| extraction_meta | jsonb | model used, token count, latency |

### `transactions`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| statement_id | uuid | FK statements, nullable for manual entries |
| card_id | uuid | FK cards, nullable for cash transactions |
| transaction_date | date | |
| posting_date | date | nullable |
| merchant_raw | text | exactly as it appears on statement |
| merchant_id | uuid | FK merchants |
| description | text | optional user note |
| amount_native | numeric(14,2) | in card currency |
| native_currency | text | SGD or USD |
| amount_sgd | numeric(14,2) | converted using `fx_rate_used` |
| fx_rate_used | numeric(12,6) | nullable for SGD transactions |
| category_id | uuid | FK categories |
| category_overridden | boolean | true if user changed from suggestion |
| split_type | text | joint, personal_a, personal_b |
| owner_user_id | uuid | FK users, who paid |
| is_subscription_candidate | boolean | flagged by detector |
| created_by | uuid | FK users |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `merchants`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| normalized_name | text | unique, used for matching |
| display_name | text | clean version for UI |
| default_category_id | uuid | FK categories |
| user_override_category_id | uuid | nullable, takes precedence |
| confidence | numeric(3,2) | from LLM, 0 to 1 |
| times_seen | int | counter |
| last_seen_at | timestamptz | |

### `categories`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| name | text | "Groceries", "Transport", "Dining" |
| parent_id | uuid | nullable, for subcategories |
| color_hex | text | for charts |
| is_archived | boolean | default false |

### `budgets`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| category_id | uuid | FK categories |
| period | text | monthly, annual |
| amount_sgd | numeric(14,2) | |
| applies_to | text | couple, user_a, user_b |
| effective_from | date | |
| effective_to | date | nullable |

### `goals`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| name | text | "Japan trip", "Emergency fund" |
| target_amount_sgd | numeric(14,2) | |
| current_amount_sgd | numeric(14,2) | |
| target_date | date | nullable |
| linked_category_id | uuid | nullable, for tracking via category spend |
| created_by | uuid | FK users |

### `fx_rates`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| from_currency | text | always USD in v1 |
| to_currency | text | always SGD in v1 |
| rate | numeric(12,6) | user provided per upload |
| effective_date | date | |
| source | text | "user_input", future: "api" |
| entered_by | uuid | FK users |

### `audit_log`
| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| table_name | text | which table changed |
| record_id | uuid | which row |
| action | text | insert, update, delete |
| changed_by | uuid | FK users |
| changed_at | timestamptz | |
| diff | jsonb | before and after for changed fields |

### Row Level Security

Both users see all rows. RLS is enabled with a simple policy: authenticated users can read and write all rows. This is acceptable because there are only two users and the threat model does not include hiding data between them.

## 7. Key Features

### 7.1 Manual transaction entry

Mobile friendly Quick Add form on the home page. Required fields: date, amount, merchant, card. Optional: description, split type, category override. Defaults: today's date, last used card, joint split. Form submits in one tap on mobile.

### 7.2 Statement upload

Drag and drop or tap to upload. Supports PDF (multi page) and images (JPG, PNG). On upload, user selects the card the statement belongs to, the period, and the FX rate (if USD card). The system rasterizes PDFs to images at 200 DPI, sends each page to Claude, parses the JSON response into staged transactions, and routes the user to the Review Queue.

The extraction prompt requests a strict JSON schema: array of `{date, posting_date, merchant_raw, amount_native, type}` where type is debit or credit. Refunds are handled as credits and shown with negative sign in totals.

### 7.3 Review Queue

Table view of all pending transactions from a specific upload. Each row is editable inline: date, merchant, amount, category, split type. Bulk actions: confirm all, mark all as joint, apply category to all matching merchant. After confirmation, transactions move to the main `transactions` table.

### 7.4 Categorization

When a transaction enters the system:
1. Normalize merchant string (uppercase, strip "PTE LTD", strip city codes like "SG", strip card scheme noise)
2. Look up in `merchants` table
3. If hit, apply category. If override exists, use override
4. If miss, call Claude with merchant string and known categories. Store result with `confidence`
5. User can override on the Review Queue or any transactions page. Override saves to `merchants.user_override_category_id` so future transactions match

### 7.5 USD handling

When uploading a USD card statement, the user inputs the FX rate to use for that statement. This rate is stored in `fx_rates` and applied to all transactions in that statement to populate `amount_sgd`. The rate is per upload, not per transaction, but can be edited per transaction if needed.

### 7.6 Joint versus personal tagging

Default tag on every transaction is `joint`. User can flip individual transactions or bulk select. The dashboard shows three views: couple total (all joint plus both personals), user A only (joint share plus personal A), user B only (joint share plus personal B). Joint share defaults to 50/50, configurable in Settings.

### 7.7 Subscription detector

Runs on demand from the Subscriptions page. Scans the last 90 days of transactions and groups by normalized merchant. A merchant is flagged as a subscription if:

1. It appears at least 3 times
2. The intervals between transactions are within 7 days of monthly (25 to 35 day cadence)
3. Amounts are within 10% of each other across occurrences

The page shows total monthly subscription burn, list of detected subscriptions, and a "mark as not subscription" button to suppress false positives.

### 7.8 Budgets

Two layers:
1. Monthly budget per category
2. Annual budget per category (useful for travel, gifts)

Each budget has an `applies_to` field: couple, user A, or user B. Dashboard shows progress bars per category with rollover indicator if a category was under or over the previous month.

### 7.9 Goals

Savings or spending targets. A goal has a target amount, optional target date, and optional linked category. If linked, the goal pulls progress from cumulative spend in that category (useful for trip funds where you log expenses against the trip). If unlinked, progress is manually updated.

### 7.10 Audit log

Every insert, update, and delete on transactions, budgets, goals, and merchants is logged. The Settings page has an Audit Log view filterable by user, table, and date range. Implemented via Postgres triggers writing to `audit_log` automatically.

### 7.11 Dashboard

Single page with these modules in order:

1. Top strip: this month spend, last month spend, year to date spend. Three numbers each shown three ways (couple, user A, user B)
2. Budget progress: bar chart of categories vs monthly budget, current month
3. Spend by category: donut chart for current month, stacked bar by month for last 12 months
4. Subscription burn: monthly subscription total, top five subscriptions
5. Goals: progress bars for active goals
6. Recent transactions: last 20 transactions with quick edit

All charts use Plotly. Mobile layout reflows to single column.

### 7.12 Export

Settings page has an Excel export button. User selects date range and export format (transactions only, or full report with budget tracking, category summaries, monthly trends). Output is a multi sheet xlsx file generated with openpyxl.

## 8. Pages and Routes

| Page | Purpose | Mobile priority |
|---|---|---|
| Login | Supabase auth | High |
| Home (Dashboard) | Default landing | High |
| Quick Add | Single screen manual entry | Highest |
| Upload | Statement upload and FX entry | Medium |
| Review Queue | Confirm extracted transactions | Medium |
| Transactions | Full history with filters | Medium |
| Subscriptions | Detection results | Medium |
| Budgets | View and edit budgets | Medium |
| Goals | View and edit goals | Medium |
| Settings | Cards, categories, FX, audit log, export | Low |

Streamlit multi page app structure. Each page is a separate file in `pages/`.

## 9. Phased Delivery

### Phase 1: MVP

Goal: get the data model right, prove out manual workflow, validate categorization approach without spending on LLM extraction.

In scope:
- Supabase setup, auth, all tables, RLS
- Streamlit shell with login, navigation, mobile responsive layout
- Manual transaction entry (Quick Add)
- Cards management
- Categories management with seed data (15 default categories)
- Merchant database and rule based categorization (LLM categorization stub returning "Uncategorized" for unknown merchants, user fills in)
- Transactions page with filters, inline edit, bulk operations
- Basic dashboard: monthly spend by category, this month vs last month, individual and couple totals
- Joint vs personal tagging
- USD with manual FX per transaction
- Audit log via Postgres triggers
- CSV export

Out of scope: PDF or image upload, LLM categorization, budgets, goals, subscription detector, Excel export.

Exit criteria: both users have logged one full month of expenses manually, dashboard reflects accurate totals, no data integrity issues.

### Phase 2: LLM extraction and categorization

In scope:
- Anthropic API integration
- PDF and image upload pipeline
- Statement extraction with Claude vision
- Review Queue page
- LLM categorization for unknown merchants
- FX rate per upload (replacing per transaction)

Exit criteria: a 30 transaction statement is extracted, reviewed, and posted in under five minutes end to end.

### Phase 3: Budgets, goals, subscriptions, polish

In scope:
- Budgets monthly and annual
- Goals
- Subscription detector
- Excel export with multi sheet report
- Dashboard upgrades (subscription burn module, goals progress, year to date views)
- Mobile UI polish

Exit criteria: the app fully replaces the spreadsheet currently in use.

### Phase 4: Nice to have

- FX rate auto fetch from a free API (frankfurter.app or similar)
- Receipt photo attachment per transaction
- Annual review report
- Anomaly alerts (unusual category spend month over month)
- Telegram bot for one tap entry on mobile

## 10. Repository Structure

```
couple-expense-tracker/
├── README.md
├── TECHNICAL_BRIEF.md
├── .gitignore
├── .env.example
├── requirements.txt
├── pyproject.toml
├── streamlit_app.py
├── pages/
│   ├── 01_quick_add.py
│   ├── 02_upload.py
│   ├── 03_review_queue.py
│   ├── 04_transactions.py
│   ├── 05_subscriptions.py
│   ├── 06_budgets.py
│   ├── 07_goals.py
│   └── 08_settings.py
├── src/
│   ├── __init__.py
│   ├── db.py
│   ├── auth.py
│   ├── models.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── pdf_to_images.py
│   │   ├── claude_extractor.py
│   │   └── prompts.py
│   ├── categorization/
│   │   ├── __init__.py
│   │   ├── normalizer.py
│   │   ├── merchant_cache.py
│   │   └── llm_categorizer.py
│   ├── fx.py
│   ├── budgets.py
│   ├── goals.py
│   ├── subscriptions.py
│   ├── audit.py
│   └── export.py
├── sql/
│   ├── 001_init_schema.sql
│   ├── 002_seed_categories.sql
│   ├── 003_audit_triggers.sql
│   └── 004_rls_policies.sql
├── tests/
│   ├── test_normalizer.py
│   ├── test_subscriptions.py
│   ├── test_fx.py
│   └── test_extraction.py
└── docs/
    ├── deployment.md
    ├── claude_prompt_library.md
    └── runbook.md
```

## 11. Security and Privacy

1. All API keys in Streamlit secrets, never in code
2. Supabase service role key only used server side
3. Statement files in Supabase Storage with private bucket, signed URLs for download
4. RLS enabled on all tables
5. Audit log retains all writes for accountability between the two users
6. No third party trackers, no analytics SDKs
7. Sensitive fields (last_four of cards) stored but never logged or sent to LLM
8. When sending statement images to Claude, the prompt instructs to extract last four only, never full PAN

## 12. Costs

| Item | Estimate |
|---|---|
| Supabase | Free tier (500 MB db, 1 GB storage, well within limits) |
| Streamlit Community Cloud | Free |
| Anthropic API extraction | ~5 cents per statement, 6 statements per month = SGD 0.50 per month |
| Anthropic API categorization | ~0.1 cent per new merchant, drops near zero after a few months |
| Domain (optional) | SGD 15 per year |

Total expected: under SGD 5 per month at steady state.

## 13. Risks and Open Questions

1. Claude vision extraction accuracy on Singapore bank statements (DBS, OCBC, UOB, Citi, HSBC) is unproven for this exact use case. Mitigation: Phase 2 includes a Review Queue specifically because a human in the loop is mandatory until accuracy is validated over several months.
2. Streamlit Cloud has cold starts and a 1 GB resource limit. For two users this is fine, but if app feels sluggish, fallback is a small VPS for SGD 6 per month.
3. FX rate per upload is a simplification. If both users travel and use the USD card across multiple weeks at different rates, per transaction override is available but adds friction. Acceptable tradeoff for v1.
4. Mobile UX in Streamlit is functional but not native quality. If quick add friction proves too high, Phase 4 adds a Telegram bot that posts to Supabase directly.
5. Supabase free tier limits: if storage of statement PDFs exceeds 1 GB (unlikely for two users for many years), upgrade to Pro at USD 25 per month.

## 14. Success Metrics

1. Monthly tracking time under 30 minutes per month
2. Categorization hit rate above 85% after 3 months (transactions auto categorized correctly without override)
3. Zero data integrity issues (no orphaned transactions, no double counted statements)
4. Both users actively using the app within 2 weeks of Phase 1 launch
5. Subscription detector finds at least 80% of actual recurring charges within 3 months of usage

## 15. Out of Scope, Explicitly

1. Real time bank connections through aggregators
2. Investment tracking (separate workflow exists)
3. Crypto wallets
4. Tax filing automation
5. Bill splitting beyond joint and personal (no Splitwise style ledger)
6. Multi household, multi family
7. Receipt OCR for non statement items (paper receipts at hawkers, taxis, etc)

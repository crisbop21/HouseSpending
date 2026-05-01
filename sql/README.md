# SQL migrations

Apply these in numeric order via the Supabase SQL editor. Never edit a migration in place once it has been applied to a real environment; add a new one instead.

Planned files (created in Phase 1.A):

- `001_init_schema.sql`     all tables from `TECHNICAL_BRIEF.md` section 6
- `002_seed_categories.sql` 15 default categories with color hex
- `003_audit_triggers.sql`  audit log function plus triggers
- `004_rls_policies.sql`    row level security policies

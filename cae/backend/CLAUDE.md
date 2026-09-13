# CAE backend

Loads when you work under `cae/backend/`. Repo-wide rules — the non-negotiable
design rule, the gotchas list, conventions — live in the root
[CLAUDE.md](../../CLAUDE.md) and still apply.

## Tests

Backend has a pytest suite; **run it before reporting a backend change done.**

```bash
cd cae/backend
pip install -r requirements-dev.txt
pytest                              # or: pytest --cov=app --cov-report=term-missing
```

The suite runs entirely against **in-memory SQLite** — no Postgres, no Redis, no
Docker. `tests/conftest.py` carries the Postgres→SQLite shims that make that
work (JSONB compiled as JSON, `gen_random_uuid()` defaults stripped,
string-tolerant UUID binds). If you add a model using a Postgres-specific type,
expect to extend those shims. Layout is documented in
[`tests/README.md`](tests/README.md).

Note `rules/test_registry.py` **executes every registered rule against an empty
schema** — so a new rule with invalid DuckDB SQL fails there, and a new rule that
queries a table `rules/schema.py` doesn't define will too. Add the table shape
there when you add the rule.

## Rule registry

`app/rules/__init__.py` is a decorator registry: `@register("SAL-001")` maps a
rule code to a callable, and the module's tail imports every rule module to
trigger registration.

A rule is `fn(conn, company_id, rule)` returning a **list of exception dicts**
with keys `title`, `description`, `severity`, `financial_impact`, `evidence`.
To add one: write the function in the right pack with the next code in sequence,
decorate it, and ensure a corresponding `AuditRule` row exists (rules are
enabled/disabled from the DB, not from code).

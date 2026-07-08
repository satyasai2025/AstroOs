---
name: AstroOS Alembic PostgreSQL enum migration pattern
description: Creating PG enums in Alembic migrations requires explicit SQL + postgresql.ENUM(create_type=False) to avoid double-creation errors.
---

## Rule
In Alembic migrations, always create PostgreSQL enum types via explicit `op.execute(sa.text("DO $$ ... CREATE TYPE IF NOT EXISTS ..."))`, then use `postgresql.ENUM(name=..., create_type=False)` for column definitions inside `op.create_table`.

## Why
`sa.Enum(..., create_type=False)` inside `op.create_table` does NOT reliably suppress auto-creation in SQLAlchemy 2.x. The `_on_table_create` event fires regardless and emits `CREATE TYPE`, causing `DuplicateObject` errors if the type was already created earlier in the same transaction. Using `postgresql.ENUM(create_type=False)` is more reliable but still needs the explicit SQL guard for idempotency.

## How to apply
```python
# In upgrade():
conn = op.get_bind()
conn.execute(sa.text(
    "DO $$ BEGIN "
    "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'my_enum') THEN "
    "    CREATE TYPE my_enum AS ENUM ('a', 'b'); "
    "  END IF; "
    "END $$"
))
op.create_table("my_table",
    sa.Column("col", postgresql.ENUM("a", "b", name="my_enum", create_type=False), ...),
    ...
)

# In downgrade():
op.drop_table("my_table")
conn.execute(sa.text("DROP TYPE IF EXISTS my_enum"))
```

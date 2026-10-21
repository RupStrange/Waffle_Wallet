# Spec: Filter Transactions

## 1. Overview

Implement a read-only JSON API for querying a user's expenses. Steps 1–4 established the
database, registration, login/logout, and the profile UI. This step adds the backend read
path: `GET /api/expenses` accepts query-parameter filters (category, date range, amount
range), a sort order, and pagination, and returns a typed JSON envelope.

Frontend changes (wiring `main.js` to `fetch()`) and text search over `description` are
**Step 06** — not part of this spec.

## 2. Dependencies

Reuse existing components:

- `models/expense.py` — `Expense` ORM model, `VALID_CATEGORIES` tuple.
- `models/user.py` — `User` model (returned by `get_current_user`).
- `database/database.py` — `engine`, `SessionLocal`, `Base`.
- `dependencies.py` — `get_db`, `get_current_user`.
- `schemas/expense.py` — `ExpenseResponse` (already defined with `from_attributes = True`).
- `crud/users.py` — pattern for `select()` + `db.scalars()` style.

Do not duplicate session setup, password utilities, or authentication logic.

## 3. Routes

| Method | Path | Name | Auth |
|---|---|---|---|
| `GET` | `/api/expenses` | `api_list_expenses` | Required — raises HTTP 401 |

No HTML route is added. The `/api` prefix separates this endpoint from the Jinja2 HTML routes
and enables path-prefix–based error handler routing (see §7).

## 4. Files to Create

### `crud/expenses.py`

Implement one function:

```python
def list_expenses(
    db: Session,
    user_id: int,
    filters: ExpenseFilters,
) -> tuple[Sequence[Expense], int]:
```

- `user_id` is a **required positional argument**, never a field of `filters`. This is the
  IDOR guard: identity comes from the session, never from the request.
- Build a `conditions` list initialised with `Expense.user_id == user_id`. Add one condition
  per filter that is `is not None` (not a truthiness check — `Decimal("0")` is falsy).
- Build one `filtered` statement via `select(Expense).where(*conditions)`.
- Derive `total` from that statement: `select(func.count()).select_from(filtered.subquery())`.
  Both queries share one object so they cannot drift if a join or DISTINCT is added later.
- Apply sort from `SORT_OPTIONS` (an `{str: tuple[column_expr, ...]}` allowlist mapping sort
  keys to ORM column objects — the user never supplies an identifier). Always include
  `Expense.id` as a tie-breaker in every sort tuple to guarantee deterministic pagination.
- Apply `.limit(filters.limit).offset(filters.offset)` after ordering.
- Use `db.scalars(...).all()` and `db.scalar(...)` — never `db.query()`.

### `routers/api_expenses.py`

Single route:

```python
@router.get("", name="api_list_expenses", response_model=ExpenseListResponse)
async def api_list_expenses(
    filters: Annotated[ExpenseFilters, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseListResponse:
```

- Path is `""`, not `"/"`. With `prefix="/api/expenses"`, a trailing slash causes a 307
  redirect from the clean URL.
- Route body is two lines: call `crud_expenses.list_expenses`, return `ExpenseListResponse`.
  No conditionals, no DB logic.
- Register with `app.include_router(api_expenses.router)` in `main.py`.

### `errors/exceptions.py`

Custom exception hierarchy:

```python
class AppException(Exception):
    status_code: int = 500
    code: str = "internal_error"

class NotFoundError(AppException):   status_code = 404; code = "not_found"
class BadRequestError(AppException): status_code = 400; code = "bad_request"
class UnauthorizedError(AppException): status_code = 401; code = "unauthorized"
class ForbiddenError(AppException):  status_code = 403; code = "forbidden"
class ConflictError(AppException):   status_code = 409; code = "conflict"
```

### `errors/handlers.py`

Register handlers for every exception type. All return the same JSON envelope:

```json
{"error": {"code": "...", "message": "...", "details": {}}}
```

Handler registration order (most specific first — a later handler for a parent class silently
replaces an earlier one for a child):

1. `AppException`
2. `RequestValidationError`
3. `IntegrityError`
4. `SQLAlchemyError`
5. `StarletteHTTPException`
6. `Exception` (catch-all — logs `traceback.format_exc()` server-side, returns only a
   generic message to the client; never expose stack traces)

Expose `register_exception_handlers(app: FastAPI) -> None` as the public interface.

### `errors/__init__.py`

Re-export all exception classes and `register_exception_handlers`.

### `tests/conftest.py`

Shared pytest fixtures using SQLite in-memory + `StaticPool`:

- `db_session` — creates engine, `Base.metadata.create_all`, yields session, then close +
  `drop_all`. **`import models` at module level** (`# noqa: F401`) before `create_all` — without
  it, `Base.metadata` sees no tables.
- `seed_users` — inserts user A (Alice) and user B (Bob), returns both.
- `make_expense` — factory fixture; each test seeds its own data shape.
- `client` — overrides `get_db` and `get_current_user` (→ user A); clears overrides in
  teardown via `yield`.
- `client_as_b` — same pattern for user B.

**Never use `with TestClient(app)`** — the context manager fires the lifespan and runs
`seed_db()` against the real PostgreSQL database.

**Always `app.dependency_overrides.clear()` in teardown** — it is global mutable state on
`app` and leaks into other test files if left set.

### `tests/test_expense_filters.py`

Full test suite — see §8 for the complete list of cases.

### `pytest.ini`

```ini
[pytest]
testpaths = tests
```

## 5. Files to Modify

### `schemas/expense.py`

Add:

```python
SORT_TYPE = Literal["date-desc", "date-asc", "amt-desc", "amt-asc"]

class ExpenseFilters(BaseModel):
    model_config = {"extra": "forbid"}
    category: CATEGORY_TYPE | None = None
    start_date: date | None = None        # inclusive
    end_date: date | None = None          # inclusive
    min_amount: Decimal | None = Field(default=None, ge=0)
    max_amount: Decimal | None = Field(default=None, ge=0)
    sort: SORT_TYPE = "date-desc"
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_ranges(self) -> "ExpenseFilters":
        if self.start_date is not None and self.end_date is not None \
                and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        if self.min_amount is not None and self.max_amount is not None \
                and self.min_amount > self.max_amount:
            raise ValueError("min_amount cannot exceed max_amount")
        return self

class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    limit: int
    offset: int
```

`CATEGORY_TYPE` is derived from `models/expense.py:VALID_CATEGORIES` via
`Literal[VALID_CATEGORIES]` — `schemas/expense.py` is not a new copy of the category list.

Key constraints:
- `limit` ceiling is `le=100`, not higher — prevents the client from issuing a free DoS.
- `extra="forbid"` — a typo like `?categroy=Food` is a loud 422, not a silent no-op.
- `is not None` throughout — `Decimal("0")` is falsy; a truthiness check silently drops
  `min_amount=0`.

### `models/expense.py`

- Expose `VALID_CATEGORIES` as the canonical tuple (single source of truth).
- Derive `_CATEGORY_SQL_LIST` from it for the `CheckConstraint` string.
- Add composite index:
  ```python
  Index("ix_expenses_user_id_date", "user_id", "date")
  ```
  Column order: equality column (`user_id`) first, range/sort column (`date`) second. This
  serves `WHERE user_id = ?` alone, `user_id = ? AND date BETWEEN …`, and `ORDER BY date`
  without a sort step.

  **Caveat:** `create_all()` does not add indexes to existing tables. Apply by Alembic
  migration (see §5 `alembic/`).

### `dependencies.py`

- Add `-> User` return annotation to `get_current_user`.
- Give both 401 raises a `detail=` message:
  - `"Not authenticated"` — no session cookie.
  - `"Session is no longer valid"` — cookie present but user deleted.

### `main.py`

- Call `register_exception_handlers(app)` immediately after `app = FastAPI(...)`.
- Remove the old inline `@app.exception_handler(StarletteHTTPException)` block.
- Add `from routers import api_expenses` and `app.include_router(api_expenses.router)`.
- Remove `init_db()` from the lifespan — Alembic owns the schema; only `seed_db()` runs.

### `requirements.txt`

Pin Starlette to resolve a version conflict with FastAPI 0.115.5:

```
starlette>=0.40.0,<0.42.0
```

### `alembic/` (migration)

Apply the composite index to the existing database:

```python
# in the generated revision
def upgrade() -> None:
    op.create_index("ix_expenses_user_id_date", "expenses", ["user_id", "date"])

def downgrade() -> None:
    op.drop_index("ix_expenses_user_id_date", table_name="expenses")
```

Always read the generated revision before applying it. Autogenerate does not detect
`CheckConstraint` changes; those require manual `op.drop_constraint` / `op.create_check_constraint`.

## 6. Request / Response Flow

```
GET /api/expenses?category=Food&start_date=2026-01-01&sort=amt-asc&limit=20&offset=0

1. FastAPI parses query params → ExpenseFilters (Pydantic validates, cross-field checks run)
   → 422 on any violation, with {"error": {"code": "validation_error", ...}} body
2. get_current_user(request, db) reads request.session["email"]
   → 401 if missing or stale, with {"error": {"code": "unauthorized", ...}} body
3. api_list_expenses calls crud_expenses.list_expenses(db, current_user.id, filters)
4. list_expenses builds conditions, counts with subquery, fetches page
5. Returns ExpenseListResponse — Pydantic serialises Decimal as string, date as ISO-8601

Response 200:
{
  "items": [{"id": 7, "amount": "25.00", "category": "Food", "date": "2026-01-10", ...}],
  "total": 14,
  "limit": 20,
  "offset": 0
}
```

## 7. Security and Error Handling

**IDOR prevention.** `user_id` is a positional argument to `list_expenses`, not a filter
field. `conditions` is initialised with the ownership clause before any optional filter is
appended. `extra="forbid"` rejects a `?user_id=2` probe with a 422 rather than silently
ignoring it.

**SQL injection on sort.** Column identifiers cannot be parameterised by SQLAlchemy. The sort
key maps through `SORT_OPTIONS` — a hardcoded dict of ORM column expressions. The user never
supplies an identifier; an unknown key is a 422.

**Error shape.** All error responses from `/api/*` use a single envelope:
```json
{"error": {"code": "...", "message": "...", "details": {}}}
```
The catch-all `Exception` handler logs the full traceback server-side (`logging` + `traceback.format_exc()`) and returns only `"An unexpected error occurred"` to the client — no stack traces in responses.

**Decimal serialisation.** Pydantic v2 serialises `Decimal` as a JSON string (`"25.00"`), not
a float. This preserves precision: `JSON.parse` converts all JSON numbers to IEEE-754 doubles,
which can lose cents. In tests, assert `== "25.00"`.

**Known gaps (not this step):**
- `/profile`, `/account`, `/preferences` have no auth guard.
- No rate limiting on the filter endpoint.
- Text search (`q` over `description`) deferred to Step 06.

## 8. Definition of Done

### Infrastructure
- [x] `pytest.ini` created; `pytest` collects and runs the suite.
- [x] `tests/conftest.py` provides `db_session`, `seed_users`, `make_expense`, `client`, `client_as_b`.
- [x] `errors/` package created; all handlers registered; single JSON error shape throughout.
- [x] `starlette>=0.40.0,<0.42.0` pinned; `pip install -r requirements.txt` succeeds.
- [x] Alembic migration created and applied; `ix_expenses_user_id_date` present on `expenses` table.

### Schema validation (422s)
- [x] Invalid category → 422.
- [x] `start_date > end_date` → 422.
- [x] `min_amount > max_amount` → 422.
- [x] `limit > 100` → 422.
- [x] Unknown query param (e.g. `?categroy=Food`) → 422.
- [x] Injection attempt in `sort` → 422.

### Filter correctness
- [x] No filters → all user's expenses returned.
- [x] Empty result → 200 with `items == []`, not 404.
- [x] Category filter returns only matching rows.
- [x] `start_date` is inclusive.
- [x] `end_date` is inclusive.
- [x] `min_amount` is inclusive; `min_amount=0` is not dropped.
- [x] `max_amount` is inclusive.
- [x] Multiple filters are ANDed.

### Sorting and pagination
- [x] Default sort is `date-desc` (newest first).
- [x] `amt-asc` returns rows in numerically ascending amount order.
- [x] `total` is stable across pages (counts all matching rows, ignoring limit/offset).
- [x] Pages are non-overlapping and collectively exhaustive.
- [x] `offset` past end → empty page, correct `total`.
- [x] Rows with tied dates are ordered deterministically (id tie-breaker).

### Security
- [x] User A cannot see user B's expenses.
- [x] Unauthenticated request → 401 with JSON error envelope (not plain-text `None`).

### Serialisation
- [x] `amount` serialises as a decimal string (`"25.00"`), not a float.

## 9. Implementation Instructions

Before editing, read `CLAUDE.md`, existing `crud/`, `models/`, `schemas/`, and `dependencies.py`
to confirm naming conventions and layer boundaries.

Implement bottom-up: schema → model index → crud → dependencies → errors → main → router →
tests. Each layer is verifiable before the next. The schema and crud layers can be tested
without starting the web server.

After implementation, run `pytest -v` and verify all 23 tests pass. Check `/docs` to confirm
every filter param appears with its type and constraints. Optionally run a manual smoke test
with the dev server:

```
GET /api/expenses
GET /api/expenses?category=Food&sort=amt-asc
GET /api/expenses?start_date=2026-10-01&end_date=2026-10-21
GET /api/expenses?limit=2&offset=2
GET /api/expenses?category=Nope      # expect 422
```

Do not modify stub routes in `routers/expenses.py` (Steps 7–9). Do not add frontend changes
(Step 06). Do not install new pip packages.

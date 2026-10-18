# Spec Document: Waffle Wallet Database Foundation

## 1. Overview

Implement the foundational database layer for Waffle Wallet using PostgreSQL and SQLAlchemy ORM, integrated with FastAPI.

This layer will support future features, including authentication, user profiles, and expense tracking.

## 2. Dependencies

- PostgreSQL
- SQLAlchemy ORM
- Psycopg 3 PostgreSQL driver
- Pydantic
- `python-dotenv` or equivalent environment-based configuration
- A secure password-hashing library

## 3. Routes

- No new API routes.
- Existing application routes must remain unchanged.
- Database functionality must be accessible through reusable modules and dependency injection.

## 4. Database Schema

### A. `users`

| Column          | Type        | Constraints                          |
| --------------- | ----------- | ------------------------------------ |
| `id`            | Integer     | Primary key, auto-increment          |
| `name`          | String(100) | Not null                             |
| `email`         | String(255) | Unique, not null, indexed            |
| `password_hash` | String      | Not null                             |
| `created_at`    | DateTime    | Not null, server-generated timestamp |

### B. `expenses`

| Column        | Type           | Constraints                                 |
| ------------- | -------------- | ------------------------------------------- |
| `id`          | Integer        | Primary key, auto-increment                 |
| `user_id`     | Integer        | Foreign key → `users.id`, not null, indexed |
| `amount`      | Numeric(10, 2) | Not null, positive                          |
| `category`    | String(50)     | Not null                                    |
| `date`        | Date           | Not null                                    |
| `description` | Text           | Nullable                                    |
| `created_at`  | DateTime       | Not null, server-generated timestamp        |

### Relationships and Constraints

- One user can have multiple expenses.
- Every expense must belong to an existing user.
- Email addresses must be unique.
- Expense amounts must be greater than zero.
- Use appropriate SQLAlchemy relationships and PostgreSQL constraints.
- Store monetary values using `Decimal`-compatible numeric types.
- Store dates as database `DATE` values.
- Use timezone-aware timestamps where appropriate.

## 5. Project Structure

Organise the database layer into separate, maintainable modules:

```text
app/
├── main.py
├── core/
│   └── config.py
├── database/
│   ├── __init__.py
│   ├── database.py
│   └── db.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── expense.py
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   └── expense.py
└── dependencies.py
```

Responsibilities:

- `main.py`: FastAPI application and lifespan configuration.
- `core/config.py`: Environment-based configuration.
- `database/database.py`: SQLAlchemy engine, session factory, and declarative base.
- `database/db.py`: Database initialization and demo-data seeding.
- `models/`: SQLAlchemy ORM models.
- `schemas/`: Pydantic schemas for validation and serialization.
- `dependencies.py`: Reusable dependencies, including database session injection.

Keep the implementation consistent with the existing repository structure if equivalent modules already exist.

## 6. Functions to Implement

### A. `get_db()`

Implement a FastAPI-compatible database dependency.

Requirements:

- Create a SQLAlchemy session using the configured session factory.
- Yield the session to the caller.
- Close the session in a `finally` block.
- Ensure the session is closed even if an exception occurs.
- Support injection through `Depends(get_db)`.

Example:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`SessionLocal` refers to the configured SQLAlchemy session factory.

### B. `init_db()`

Implement database initialisation.

Requirements:

- Import all ORM models before creating tables.
- Create missing tables using `Base.metadata.create_all()`.
- Ensure repeated calls do not recreate existing tables.
- Handle initialisation failures with clear diagnostic information.
- Do not perform database initialisation on every API request.

Use Alembic for future schema migrations.

### C. `seed_db()`

Populate the database with initial demonstration data.

**Demo user**

- Name: `Demo User`
- Email: `demo@wafflewallet.com`
- Password: `demo123`

Requirements:

1. Check whether the demo user already exists.
2. If the user exists, return without inserting duplicate demo data.
3. Hash the password using a secure password-hashing library.
4. Create exactly eight sample expenses associated with the demo user.
5. Include at least one expense for each of the seven defined categories.
6. Spread the expense dates across the current month.
7. Use realistic positive monetary amounts represented as `Decimal`.
8. Commit the user and expenses in a transaction.
9. Roll back the transaction if seeding fails.
10. Never store plaintext passwords.

## 7. FastAPI Integration

Integrate database initialisation with the FastAPI application lifecycle.

Requirements:

- Use FastAPI's lifespan mechanism for startup initialisation.
- Ensure database initialisation completes before the application serves requests.
- Initialise the database and seed demo data in the appropriate startup sequence.
- Reuse the shared SQLAlchemy engine and session factory.
- Inject database sessions into routes through `Depends(get_db)`.
- Do not create a new engine or session factory for each request.
- Ensure resources are disposed of appropriately during application shutdown.
- Fail startup clearly if required database initialisation cannot complete.

Use synchronous SQLAlchemy consistently throughout this implementation unless the existing application explicitly requires an asynchronous database stack.

## 8. PostgreSQL Configuration

Configure the database through environment variables.

Example `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:1@localhost:5432/waffle_wallet
```

Requirements:

- Use PostgreSQL as the application's database.
- Keep database credentials outside source code.
- Add an `.env.example` containing placeholder credentials.
- Exclude `.env` from version control.
- Validate required configuration during startup.
- Provide clear connection-error diagnostics without exposing secrets.
- Configure suitable connection pooling and connection health checks where appropriate.

## 9. Fixed Expense Categories

Use exactly these category values:

- Food
- Transport
- Bills
- Health
- Entertainment
- Shopping
- Other

Validate category values at the application level. Use a database constraint if necessary to ensure invalid categories cannot be persisted through other database access paths.

## 10. Implementation Rules

- Use SQLAlchemy ORM for database operations.
- Use declarative SQLAlchemy models.
- Keep ORM models separate from Pydantic schemas.
- Use SQLAlchemy sessions for persistence and queries.
- Use `Depends(get_db)` for FastAPI database dependency injection.
- Use transactions for operations that must succeed or fail together.
- Use parameterised ORM expressions rather than constructing SQL through string formatting.
- Keep database configuration centralised.
- Follow secure password-storage practices.
- Never expose password hashes in API responses.
- Use appropriate type hints and clear function names.
- Avoid unnecessary dependencies and unrelated code changes.
- Keep the database layer modular and suitable for future expansion.

## 11. Expected Behaviour

### Database initialisation

- Creates the required tables.
- Registers all declared ORM models.
- Can be safely invoked repeatedly.
- Reports connection or schema-creation errors clearly.

### Database sessions

- Provides a usable SQLAlchemy session.
- Closes sessions reliably.
- Supports dependency injection into FastAPI routes.

### Demo data

- Creates one demo user and eight expenses when the demo user does not exist.
- Covers all seven expense categories.
- Prevents duplicate seed data on repeated runs.
- Stores a hashed password.
- Preserves foreign key relationships.
- Rolls back incomplete transactions.

### Data integrity

- Duplicate email addresses are rejected.
- Expenses cannot reference nonexistent users.
- Non-positive expense amounts are rejected.
- Monetary precision is preserved.
- Invalid expense categories are rejected.

## 12. Error Handling

- Handle database connection failures with clear diagnostic messages.
- Roll back transactions when database operations fail.
- Ensure database sessions are closed reliably.
- Preserve database integrity constraints.
- Avoid returning internal database errors or credentials to clients.
- Log actionable debugging information without logging sensitive data.

## 13. Definition of Done

- [ ] PostgreSQL connection is configured through environment variables.
- [ ] SQLAlchemy engine and session factory are implemented.
- [ ] User and expense ORM models are implemented.
- [ ] Database relationships and constraints are configured.
- [ ] Pydantic schemas are separated from ORM models.
- [ ] `get_db()` correctly manages session lifecycle.
- [ ] `init_db()` creates the required tables.
- [ ] FastAPI lifespan integration is complete.
- [ ] Demo user is created with a securely hashed password.
- [ ] Eight sample expenses cover all seven categories.
- [ ] Repeated seeding does not create duplicates.
- [ ] Transaction rollback is verified.
- [ ] Database constraints are tested.
- [ ] Application startup and database connectivity are verified.
- [ ] Existing routes and functionality remain unchanged.
- [ ] Configuration and setup instructions are documented.

## 14. Scope Restrictions

This task establishes the database foundation only.

Do not implement registration, login, authentication workflows, profile management, or expense CRUD endpoints in this step.

Do not redesign the frontend or change existing API contracts.

The final implementation must provide a clean, maintainable, production-oriented PostgreSQL and SQLAlchemy foundation for future Waffle Wallet features.

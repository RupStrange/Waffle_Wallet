# Spec: Registration

## Overview

Implement user registration for Waffle Wallet. A visitor fills in their name, email, and password on the existing `/register` page; the server validates the input, hashes the password with passlib/bcrypt, inserts a new row into the `users` table, and redirects to the login page on success. This step turns the static register template into a working form and is the prerequisite for every authenticated feature that follows.

## Depends on

- Step 1 — Database Foundation (users table, SQLAlchemy engine, `SessionLocal`, `User` model)

## Routes

- `POST /register` — accept registration form, validate, insert user, redirect — public

## Database changes

No database changes. The `users` table and `User` model are already defined in Step 1.

## Templates

- **Modify:** `templates/register.html` — add `<form method="post" action="/register">` with fields `name`, `email`, `password`, `confirm_password`; display server-side validation errors inline

## Files to change

- `routers/pages.py` — add `POST /register` handler (name: `register_post`)
- `templates/register.html` — add form markup and error display

## Files to create

- `crud/users.py` — `get_user_by_email(db, email)` and `create_user(db, name, email, password_hash)`
- `services/registration.py` — `register_user(db, name, email, password, confirm_password)` — validates input, checks uniqueness, hashes password, calls crud

## New dependencies

No new dependencies. `passlib[bcrypt]` is already in `requirements.txt`.

## Rules for implementation

- SQLAlchemy ORM only — no raw SQL
- Parameterised ORM expressions only — no string formatting in queries
- Passwords hashed with `passlib.context.CryptContext(schemes=["bcrypt"])`
- Never store or log plaintext passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route handler has one responsibility: call the service, return a response
- Validation errors re-render the form with the error message — never redirect on failure
- Duplicate email → field-level error, not a 500
- On success → `RedirectResponse` to `/login` with status 303
- Name the POST route `register_post` so `url_for` resolves it

## Definition of done

- [ ] `GET /register` still renders the form (no regression)
- [ ] Submitting a valid form creates a new row in `users` with a bcrypt hash
- [ ] Submitting with mismatched passwords re-renders the form with an error message
- [ ] Submitting with an already-registered email re-renders the form with an error message
- [ ] Submitting with an empty name or email re-renders the form with an error message
- [ ] Successful registration redirects to `/login` (HTTP 303)
- [ ] Password field value is never echoed back in the rendered HTML
- [ ] The demo user created by `seed_db` is unaffected
- [ ] No plaintext password appears in the database or application logs

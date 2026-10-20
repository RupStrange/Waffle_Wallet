# Spec: Login and Logout

## 1. Overview

Implement cookie-backed session authentication for Waffle Wallet. Step 1 established the database foundation, and Step 2 implemented registration.

This step adds login, logout, a reusable `get_current_user` dependency, and an authentication-aware navbar.

## 2. Dependencies

Reuse existing components:
- SQLAlchemy `User` model, engine, and `SessionLocal`.
- Database session dependency and application settings.
- `crud/users.py:get_user_by_email`.
- `pwd_context` from `database/db.py`.
- Registration conventions and the per-field error pattern in `templates/register.html`.

Do not duplicate existing models, database configuration, or password utilities.

## 3. Routes

- `GET /login`: Existing route in `routers/pages.py`; preserve its name and behavior.
- `POST /login`: Create in `routers/auth.py`, named `login_post`. Authenticate the user and redirect to `/profile` with HTTP 303.
- `GET /logout`: Create in `routers/auth.py`, named `logout`. Clear the session, expire the cookie, and redirect to `/` with HTTP 303.

`GET /login` and `POST /login` share a URL but use different HTTP methods.

Remove the existing inline `GET /logout` stub from `main.py`. Retain GET logout for compatibility with the current navbar; consider POST logout with CSRF protection in a future security-hardening step.

## 4. Files to Create

### `routers/auth.py`

- Implement `POST /login` and `GET /logout`.
- Use the existing database dependency.
- Delegate credential verification to `services/authentication.py`.
- Handle authentication errors and render the login template on failure.
- Establish and clear session data.
- Use named routes and HTTP 303 redirects.

### `services/authentication.py`

Implement:
- `AuthenticationError`: exception for failed authentication.
- `authenticate_user(db, email, password)`: retrieve the user through the existing CRUD function and verify the password.

Return the SQLAlchemy `User` object on success. Raise `AuthenticationError` for an unknown email or incorrect password.

Reuse `pwd_context` from `database.db`. Do not perform HTTP handling, raw SQL, or database queries outside CRUD functions.

## 5. Files to Modify

### `main.py`

- Register Starlette's `SessionMiddleware` before including routers.
- Obtain the signing key from `get_settings().secret_key`; never hardcode it.
- Configure `same_site="lax"`.
- Enable `https_only=True` in production HTTPS deployments and allow local HTTP development.
- Include the authentication router and remove the inline logout stub.

### `dependencies.py`

Implement `get_current_user`:
1. Read `user_id` from `request.session`.
2. Raise `HTTPException(status_code=401)` if the ID is missing or invalid.
3. Retrieve the user through CRUD using the existing database session.
4. Raise HTTP 401 if the user no longer exists.
5. Return the authenticated SQLAlchemy `User` object.

Do not create another database dependency or implement redirects here. Protected HTML routes can redirect unauthenticated users to `/login`.

### `templates/login.html`

- Keep extending `base.html`.
- Set the form action to `url_for('login_post')` and method to POST.
- Preserve the submitted email after failure.
- Use the per-field `errors` dictionary pattern from `register.html`.
- Ensure the initial GET renders without Jinja2 undefined errors.
- Never echo the password through a template `value` attribute.

Follow the existing template context conventions.

### `templates/base.html`

Update `.ww-nav-actions`:
- Authenticated session (`request.session.get('user_id')`): show `Sign out` using `url_for('logout')`.
- Signed-out session: show the existing `Sign in` and `Sign up` links using their named routes.

Preserve existing styling and CSS variables.

### `requirements.txt`

Add:

`itsdangerous>=2.2`

Starlette uses this dependency to sign session cookies. Declare it explicitly; do not add unnecessary packages.

## 6. Authentication Flow

1. Receive email and password at `POST /login`.
2. Reject an empty or whitespace-only email and an empty password before any database query.
3. Call `authenticate_user(db, email, password)`.
4. Look up the user through `crud/users.py:get_user_by_email`.
5. Verify the password with `pwd_context.verify(plaintext, user.password_hash)`.
6. On failure, raise `AuthenticationError`; the router renders the login page with the generic error message.
7. On success, clear any previous session data, store `user_id` and `user_name`, and redirect to `/profile` with HTTP 303.

Normalize email according to existing registration conventions. Never silently transform the password.

## 7. Security and Error Handling

- Use exactly `Incorrect email or password.` for both unknown emails and incorrect passwords.
- Both failure cases must have the same HTTP status and equivalent response behavior to prevent account enumeration.
- Reuse the existing bcrypt `pwd_context`; never create another `CryptContext`.
- Never compare password hashes with `==`.
- Never store or log plaintext passwords.
- Store only `user_id` and `user_name` in the session.
- Signed cookies are not encrypted; never store secrets in them.
- Clear session data on logout and ensure the response expires the cookie.
- Use `HTTPException` for HTTP errors where appropriate; never return bare strings as error responses.
- Use `url_for()` for internal links and redirects.
- SQLAlchemy ORM only; no raw SQL or f-strings in queries.
- Keep database access in `crud/`, business logic in `services/`, and HTTP handling in `routers/`.
- Reuse existing settings, models, dependencies, and project conventions.
- Do not modify unrelated functionality.

## 8. Definition of Done

### Login
- [ ] `GET /login` renders without undefined-variable errors.
- [ ] The seeded demo account `demo@wafflewallet.com` / `demo123` works if confirmed by the seed implementation.
- [ ] Registered users can log in.
- [ ] Successful login redirects to `/profile` with HTTP 303.
- [ ] A signed session cookie is issued with only `user_id` and `user_name`.
- [ ] Incorrect passwords and unknown emails return the same generic message and equivalent responses.
- [ ] Empty email or password is rejected before any database query.
- [ ] Failed login does not establish an authenticated session or expose passwords.
- [ ] The email is preserved on failure, but the password is never echoed.

### Logout and navbar
- [ ] Logout clears the session, expires the cookie, and redirects to `/` with HTTP 303.
- [ ] Logout works when already signed out.
- [ ] Subsequent requests no longer carry an authenticated session.
- [ ] Signed-in users see `Sign out`; signed-out users see `Sign in` and `Sign up`.

### Dependency and project integrity
- [ ] `get_current_user` returns a valid user and raises HTTP 401 for missing sessions or deleted users.
- [ ] The inline logout stub is removed from `main.py`.
- [ ] `itsdangerous>=2.2` is declared and dependency installation succeeds in a clean environment.
- [ ] Existing registration and database functionality continue to work.

## 9. Implementation Instructions

Before editing, inspect `CLAUDE.md`, the project structure, and the relevant Step 1/Step 2 files. Confirm existing route names, settings, database dependencies, template context, and demo credentials.

Implement this specification using the existing conventions. Run relevant tests for login, logout, session handling, and `get_current_user`; verify redirects, status codes, cookie expiration, and generic errors. Report changed files, tests actually executed, and remaining issues. Do not claim unexecuted tests passed.
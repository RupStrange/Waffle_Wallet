"""
Database connection and session management.

Students will implement this file in Step 1 — Database Setup.
This module should expose:
    get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
    init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
    seed_db()  — inserts sample data for development

Example skeleton:

    import sqlite3
    from core.config import get_settings

    settings = get_settings()
    DATABASE_PATH = settings.database_url.replace("sqlite:///", "")

    def get_db():
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db():
        conn = get_db()
        with conn:
            conn.executescript(\"\"\"
                CREATE TABLE IF NOT EXISTS users (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    email     TEXT    NOT NULL UNIQUE,
                    password  TEXT    NOT NULL,
                    name      TEXT    NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS expenses (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL REFERENCES users(id),
                    amount     REAL    NOT NULL,
                    category   TEXT    NOT NULL,
                    description TEXT,
                    date       DATE    NOT NULL DEFAULT (date('now')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            \"\"\")
        conn.close()

    def seed_db():
        pass  # insert sample rows here
"""

"""SQLite schema initialization, per-user database paths, and connection helpers."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def default_database_path() -> Path:
    """Return a per-user location for the persistent library database."""
    app_data = os.environ.get("LOCALAPPDATA")
    if app_data:
        return Path(app_data) / "LibraryManagementSystem" / "library.db"
    return Path.home() / ".library_management" / "library.db"


def connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_scope(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with connection_scope(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                author TEXT NOT NULL CHECK (length(trim(author)) > 0),
                isbn TEXT,
                category TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
            CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
            CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);

            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK (length(trim(name)) > 0),
                email TEXT,
                phone TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY,
                book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
                member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
                checkout_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                CHECK (due_date >= checkout_date),
                CHECK (return_date IS NULL OR return_date >= checkout_date)
            );

            CREATE INDEX IF NOT EXISTS idx_loans_book_id ON loans(book_id);
            CREATE INDEX IF NOT EXISTS idx_loans_member_id ON loans(member_id);
            CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date);
            """
        )

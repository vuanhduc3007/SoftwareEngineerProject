"""Book model and SQLite-backed catalog create, read, update, delete, and search."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .database import connection_scope, initialize_database


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str
    isbn: str
    category: str


class BookRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialize_database(self.database_path)

    @staticmethod
    def _clean_required(value: str, field: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field} is required.")
        return cleaned

    @classmethod
    def _clean_optional(cls, value: str | None) -> str:
        return (value or "").strip()

    @staticmethod
    def _book_from_row(row: sqlite3.Row) -> Book:
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"] or "",
            category=row["category"] or "",
        )

    def list_books(self, search: str = "") -> list[Book]:
        term = search.strip()
        with connection_scope(self.database_path) as connection:
            if term:
                escaped_term = term.replace("\\", "\\\\").replace("%", "\\%").replace(
                    "_", "\\_"
                )
                pattern = f"%{escaped_term}%"
                rows = connection.execute(
                    """
                    SELECT id, title, author, isbn, category
                    FROM books
                    WHERE title LIKE ? ESCAPE '\\' COLLATE NOCASE
                       OR author LIKE ? ESCAPE '\\' COLLATE NOCASE
                       OR isbn LIKE ? ESCAPE '\\' COLLATE NOCASE
                       OR category LIKE ? ESCAPE '\\' COLLATE NOCASE
                    ORDER BY id
                    """,
                    (pattern, pattern, pattern, pattern),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, title, author, isbn, category
                    FROM books
                    ORDER BY id
                    """
                ).fetchall()
        return [self._book_from_row(row) for row in rows]

    def get_book(self, book_id: int) -> Book | None:
        with connection_scope(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, title, author, isbn, category
                FROM books
                WHERE id = ?
                """,
                (book_id,),
            ).fetchone()
        return self._book_from_row(row) if row else None

    def add_book(
        self, title: str, author: str, isbn: str = "", category: str = ""
    ) -> int:
        cleaned_title = self._clean_required(title, "Title")
        cleaned_author = self._clean_required(author, "Author")
        with connection_scope(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO books (title, author, isbn, category)
                VALUES (?, ?, ?, ?)
                """,
                (
                    cleaned_title,
                    cleaned_author,
                    self._clean_optional(isbn),
                    self._clean_optional(category),
                ),
            )
        return cursor.lastrowid

    def update_book(
        self,
        book_id: int,
        title: str,
        author: str,
        isbn: str = "",
        category: str = "",
    ) -> bool:
        cleaned_title = self._clean_required(title, "Title")
        cleaned_author = self._clean_required(author, "Author")
        with connection_scope(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE books
                SET title = ?, author = ?, isbn = ?, category = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    cleaned_title,
                    cleaned_author,
                    self._clean_optional(isbn),
                    self._clean_optional(category),
                    book_id,
                ),
            )
        return cursor.rowcount > 0

    def delete_book(self, book_id: int) -> bool:
        with connection_scope(self.database_path) as connection:
            cursor = connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        return cursor.rowcount > 0

"""Tkinter application shell for the library book catalog."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .books import Book, BookRepository
from .database import default_database_path


class BookForm(tk.Toplevel):
    """Modal dialog used to create or edit a book."""

    def __init__(
        self,
        parent: tk.Misc,
        on_save,
        book: Book | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_save = on_save
        self._book = book
        self.title("Add book / Edit book")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.title_var = tk.StringVar(value=book.title if book else "")
        self.author_var = tk.StringVar(value=book.author if book else "")
        self.isbn_var = tk.StringVar(value=book.isbn if book else "")
        self.category_var = tk.StringVar(value=book.category if book else "")

        content = ttk.Frame(self, padding=20)
        content.grid(sticky="nsew")
        fields = (
            ("Title *", self.title_var),
            ("Author *", self.author_var),
            ("ISBN", self.isbn_var),
            ("Category", self.category_var),
        )
        for row, (label, variable) in enumerate(fields):
            ttk.Label(content, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 16), pady=8
            )
            entry = ttk.Entry(content, textvariable=variable, width=48)
            entry.grid(row=row, column=1, sticky="ew", pady=8)
            if row == 0:
                self._first_entry = entry

        ttk.Label(
            content,
            text="* required. Missing values are not saved.",
        ).grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(8, 16))

        buttons = ttk.Frame(content)
        buttons.grid(row=len(fields) + 1, column=1, sticky="e")
        ttk.Button(buttons, text="Save", command=self._save).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Return>", lambda _event: self._save())
        self.bind("<Escape>", lambda _event: self.destroy())
        self._first_entry.focus_set()

    def _save(self) -> None:
        try:
            values = (
                self.title_var.get(),
                self.author_var.get(),
                self.isbn_var.get(),
                self.category_var.get(),
            )
            self._on_save(self._book.id if self._book else None, *values)
        except ValueError as error:
            messagebox.showerror("Invalid book", str(error), parent=self)
            return
        self.destroy()


class LibraryApplication(tk.Tk):
    """Main window for the Sprint 1 book catalog."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        super().__init__()
        self.title("Library Management System")
        self.geometry("980x620")
        self.minsize(760, 480)

        self.repository = BookRepository(database_path or default_database_path())
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready.")
        self._book_ids: list[int] = []

        self._build_widgets()
        self._load_books()

    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg="#2f6091", height=64)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        tk.Label(
            header,
            text="Library Management System",
            bg="#2f6091",
            fg="white",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", padx=24, pady=16)

        content = ttk.Frame(self, padding=20)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        navigation = ttk.Frame(content)
        navigation.grid(row=0, column=0, sticky="w", pady=(0, 16))
        ttk.Button(navigation, text="Books").pack(side="left", padx=(0, 10))
        ttk.Button(navigation, text="Members (later)", state="disabled").pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(navigation, text="Loans (later)", state="disabled").pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(navigation, text="Reports (later)", state="disabled").pack(
            side="left"
        )

        search_frame = ttk.Frame(content)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Search").grid(row=0, column=0, padx=(0, 12))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(search_frame, text="Search", command=self._search).grid(
            row=0, column=2, padx=(12, 8)
        )
        ttk.Button(search_frame, text="Clear", command=self._clear_search).grid(
            row=0, column=3
        )
        search_entry.bind("<Return>", lambda _event: self._search())

        table_frame = ttk.Frame(content)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        columns = ("id", "title", "author", "isbn", "category")
        self.book_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "id": "ID",
            "title": "Title",
            "author": "Author",
            "isbn": "ISBN",
            "category": "Category",
        }
        widths = {"id": 60, "title": 260, "author": 220, "isbn": 160, "category": 160}
        for column in columns:
            self.book_table.heading(column, text=headings[column])
            self.book_table.column(column, width=widths[column], anchor="w")
        self.book_table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.book_table.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.book_table.configure(yscrollcommand=scrollbar.set)
        self.book_table.bind("<Double-1>", lambda _event: self._edit_book())

        actions = ttk.Frame(content)
        actions.grid(row=3, column=0, sticky="w", pady=(16, 0))
        ttk.Button(actions, text="Add", command=self._add_book).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(actions, text="Edit", command=self._edit_book).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(actions, text="Delete", command=self._delete_book).pack(side="left")

        ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(20, 8)).grid(
            row=2, column=0, sticky="ew"
        )

    def _load_books(self, search: str = "") -> None:
        books = self.repository.list_books(search)
        for item in self.book_table.get_children():
            self.book_table.delete(item)
        self._book_ids = []
        for book in books:
            self._book_ids.append(book.id)
            self.book_table.insert(
                "",
                "end",
                values=(book.id, book.title, book.author, book.isbn, book.category),
            )
        if books:
            self.status_var.set(f"{len(books)} book(s) shown.")
        else:
            self.status_var.set("No books found.")

    def _search(self) -> None:
        self._load_books(self.search_var.get())

    def _clear_search(self) -> None:
        self.search_var.set("")
        self._load_books()

    def _selected_book(self) -> Book | None:
        selection = self.book_table.selection()
        if not selection:
            messagebox.showinfo("Select a book", "Select a book first.", parent=self)
            return None
        item_index = self.book_table.index(selection[0])
        return self.repository.get_book(self._book_ids[item_index])

    def _add_book(self) -> None:
        BookForm(self, self._save_book)

    def _edit_book(self) -> None:
        book = self._selected_book()
        if book:
            BookForm(self, self._save_book, book)

    def _save_book(
        self,
        book_id: int | None,
        title: str,
        author: str,
        isbn: str,
        category: str,
    ) -> None:
        if book_id is None:
            self.repository.add_book(title, author, isbn, category)
            self.status_var.set("Book saved successfully.")
        elif self.repository.update_book(book_id, title, author, isbn, category):
            self.status_var.set("Book updated successfully.")
        else:
            raise ValueError("The selected book no longer exists.")
        self._load_books(self.search_var.get())

    def _delete_book(self) -> None:
        book = self._selected_book()
        if not book:
            return
        if not messagebox.askyesno(
            "Delete book",
            f'Delete "{book.title}"?',
            parent=self,
        ):
            return
        if self.repository.delete_book(book.id):
            self.status_var.set("Book deleted successfully.")
            self._load_books(self.search_var.get())
        else:
            messagebox.showerror("Delete failed", "The book could not be deleted.", parent=self)


def main() -> None:
    """Start the desktop application."""
    app = LibraryApplication()
    app.mainloop()


if __name__ == "__main__":
    main()

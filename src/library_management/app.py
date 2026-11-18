"""Tkinter application shell for the library book catalog."""

from __future__ import annotations

import math
import struct
import tkinter as tk
import zlib
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from .books import Book, BookRepository
from .database import default_database_path

COLOR_PRIMARY = "#2f6091"
COLOR_PRIMARY_HOVER = "#254d75"
COLOR_BG = "#ffffff"
COLOR_SURFACE = "#e2e8f0"
COLOR_BORDER = "#cbd5e1"
COLOR_TEXT = "#1e293b"
COLOR_MUTED = "#64748b"
COLOR_DANGER = "#c53030"
COLOR_DANGER_HOVER = "#fef2f2"
COLOR_PRIMARY_LIGHT = "#eff6ff"
COLOR_ROW_SELECTED = "#d9e8f5"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def _create_rounded_rect_image(
    width: int,
    height: int,
    radius: float,
    fill_hex: str,
    border_hex: str,
    border_width: float = 1.5,
) -> tk.PhotoImage:
    w = max(4, int(width))
    h = max(4, int(height))
    fill_r, fill_g, fill_b = _hex_to_rgb(fill_hex)
    brd_r, brd_g, brd_b = _hex_to_rgb(border_hex)

    cx = w / 2.0
    cy = h / 2.0
    hx = (w - 2.0) / 2.0
    hy = (h - 2.0) / 2.0
    r = min(radius, hx, hy)
    bx = hx - r
    by = hy - r

    rows = bytearray()
    for y in range(h):
        rows.append(0)
        dy = abs((y + 0.5) - cy) - by
        for x in range(w):
            dx = abs((x + 0.5) - cx) - bx
            dist = (
                math.hypot(max(dx, 0.0), max(dy, 0.0))
                + min(max(dx, dy), 0.0)
                - r
            )

            outer_cov = max(0.0, min(1.0, 0.5 - dist))
            if outer_cov <= 0.0:
                rows.extend((0, 0, 0, 0))
                continue

            inner_cov = max(0.0, min(1.0, 0.5 - (dist + border_width)))
            t = inner_cov / outer_cov

            red = int(brd_r * (1.0 - t) + fill_r * t + 0.5)
            green = int(brd_g * (1.0 - t) + fill_g * t + 0.5)
            blue = int(brd_b * (1.0 - t) + fill_b * t + 0.5)
            alpha = int(outer_cov * 255.0 + 0.5)
            rows.extend((red, green, blue, alpha))

    def _png_chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=6))
        + _png_chunk(b"IEND", b"")
    )
    return tk.PhotoImage(data=png_bytes)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command=None,
        variant: str = "secondary",
        state: str = "normal",
        padx: int = 18,
        pady: int = 7,
        radius: float = 6.0,
    ) -> None:
        self._command = command
        self._state = state
        self._radius = radius

        if variant == "primary":
            self._bg, self._fg, self._border, self._hover_bg = (
                COLOR_PRIMARY,
                "#ffffff",
                COLOR_PRIMARY,
                COLOR_PRIMARY_HOVER,
            )
            font_tuple = ("Segoe UI", 10, "bold")
        elif variant == "danger":
            self._bg, self._fg, self._border, self._hover_bg = (
                "#ffffff",
                COLOR_DANGER,
                COLOR_DANGER,
                COLOR_DANGER_HOVER,
            )
            font_tuple = ("Segoe UI", 10)
        elif variant == "muted":
            self._bg, self._fg, self._border, self._hover_bg = (
                "#ffffff",
                COLOR_MUTED,
                COLOR_BORDER,
                "#ffffff",
            )
            font_tuple = ("Segoe UI", 10)
        else:
            self._bg, self._fg, self._border, self._hover_bg = (
                "#ffffff",
                COLOR_PRIMARY,
                COLOR_PRIMARY,
                COLOR_PRIMARY_LIGHT,
            )
            font_tuple = ("Segoe UI", 10)

        measure_font = tkfont.Font(font=font_tuple)
        width = measure_font.measure(text) + padx * 2
        height = measure_font.metrics("linespace") + pady * 2
        parent_bg = parent.cget("bg") if "bg" in parent.keys() else COLOR_BG

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2" if state == "normal" else "arrow",
        )
        self._text = text
        self._font = font_tuple
        self._normal_img = _create_rounded_rect_image(
            width, height, radius, self._bg, self._border, border_width=1.5
        )
        self._hover_img = (
            _create_rounded_rect_image(
                width, height, radius, self._hover_bg, self._border, border_width=1.5
            )
            if state == "normal"
            else self._normal_img
        )
        self._active_img = self._normal_img
        self._render()

        if state == "normal":
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<ButtonRelease-1>", self._on_click)

    def _render(self) -> None:
        self.delete("all")
        w = int(self["width"])
        h = int(self["height"])
        self.create_image(0, 0, image=self._active_img, anchor="nw")
        text_id = self.create_text(
            w / 2.0,
            h / 2.0,
            text=self._text,
            fill=self._fg,
            font=self._font,
            anchor="center",
        )
        bbox = self.bbox(text_id)
        if bbox:
            text_cx = (bbox[0] + bbox[2]) / 2.0
            text_cy = (bbox[1] + bbox[3]) / 2.0
            dx = (w / 2.0) - text_cx
            dy = (h / 2.0) - text_cy - 1.0
            self.move(text_id, dx, dy)

    def _on_enter(self, _event=None) -> None:
        self._active_img = self._hover_img
        self._render()

    def _on_leave(self, _event=None) -> None:
        self._active_img = self._normal_img
        self._render()

    def _on_click(self, event: tk.Event) -> None:
        w = int(self["width"])
        h = int(self["height"])
        if self._state == "normal" and 0 <= event.x <= w and 0 <= event.y <= h:
            if self._command:
                self._command()


class RoundedEntry(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        textvariable: tk.StringVar,
        width: int = 240,
        height: int = 36,
        radius: float = 6.0,
    ) -> None:
        parent_bg = parent.cget("bg") if "bg" in parent.keys() else COLOR_BG
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
        )
        self._radius = radius
        self._border_color = COLOR_BORDER
        self._bg_img: tk.PhotoImage | None = None

        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
        )
        self._window_id = self.create_window(12, height / 2, window=self.entry, anchor="w")

        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", lambda _e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", self._on_focus_in, add="+")
        self.entry.bind("<FocusOut>", self._on_focus_out, add="+")

    def _on_resize(self, event: tk.Event) -> None:
        w, h = event.width, event.height
        self._redraw_bg(w, h)
        self.coords(self._window_id, 12, h / 2)
        self.itemconfigure(self._window_id, width=max(20, w - 24))

    def _redraw_bg(self, w: int, h: int) -> None:
        if w < 4 or h < 4:
            return
        self.delete("bg_img")
        self._bg_img = _create_rounded_rect_image(
            w, h, self._radius, COLOR_BG, self._border_color, border_width=1.5
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw", tags="bg_img")
        self.tag_lower("bg_img")

    def _on_focus_in(self, _event=None) -> None:
        self._border_color = COLOR_PRIMARY
        self._redraw_bg(self.winfo_width(), self.winfo_height())

    def _on_focus_out(self, _event=None) -> None:
        self._border_color = COLOR_BORDER
        self._redraw_bg(self.winfo_width(), self.winfo_height())


class BookForm(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        on_save,
        book: Book | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_save = on_save
        self._book = book
        self.title("Edit Book" if book else "Add Book")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.title_var = tk.StringVar(value=book.title if book else "")
        self.author_var = tk.StringVar(value=book.author if book else "")
        self.isbn_var = tk.StringVar(value=book.isbn if book else "")
        self.category_var = tk.StringVar(value=book.category if book else "")

        content = tk.Frame(self, bg=COLOR_BG, padx=24, pady=20)
        content.grid(sticky="nsew")
        fields = (
            ("Title *", self.title_var),
            ("Author *", self.author_var),
            ("ISBN", self.isbn_var),
            ("Category", self.category_var),
        )
        for row, (label, variable) in enumerate(fields):
            tk.Label(
                content,
                text=label,
                bg=COLOR_BG,
                fg=COLOR_TEXT,
                font=("Segoe UI", 10),
            ).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=8)

            field_box = RoundedEntry(content, textvariable=variable, width=340, height=36)
            field_box.grid(row=row, column=1, sticky="ew", pady=8)
            if row == 0:
                self._first_entry = field_box.entry

        tk.Label(
            content,
            text="* required. Missing values are not saved.",
            bg=COLOR_BG,
            fg=COLOR_MUTED,
            font=("Segoe UI", 9),
        ).grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(8, 16))

        buttons = tk.Frame(content, bg=COLOR_BG)
        buttons.grid(row=len(fields) + 1, column=1, sticky="e")

        RoundedButton(buttons, text="Save", command=self._save, variant="primary").pack(
            side="left", padx=(0, 8)
        )
        RoundedButton(buttons, text="Cancel", command=self.destroy, variant="secondary").pack(
            side="left"
        )

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

class ConfirmDeleteDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.confirmed = False

        self.title("Confirm delete")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        header = tk.Frame(self, bg=COLOR_PRIMARY, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Confirm delete",
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left", padx=20)

        body = tk.Frame(self, bg=COLOR_BG, padx=20, pady=18)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Delete this book? This cannot be undone.",
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(side="top", fill="x")

        buttons = tk.Frame(body, bg=COLOR_BG)
        buttons.pack(side="bottom", fill="x")

        RoundedButton(
            buttons,
            text="Cancel",
            command=self._cancel,
            variant="secondary",
            padx=24,
            pady=8,
        ).pack(side="right")

        RoundedButton(
            buttons,
            text="Delete",
            command=self._confirm,
            variant="danger",
            padx=24,
            pady=8,
        ).pack(side="right", padx=(0, 10))

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda _event: self._cancel())
        self.bind("<Return>", lambda _event: self._confirm())

        self.update_idletasks()
        width = max(450, self.winfo_reqwidth())
        height = max(225, self.winfo_reqheight())
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _confirm(self) -> None:
        self.confirmed = True
        self.destroy()

    def _cancel(self) -> None:
        self.confirmed = False
        self.destroy()

class LibraryApplication(tk.Tk):
    SEARCH_PLACEHOLDER = "title, author, ISBN or category"

    def __init__(self, database_path: str | Path | None = None) -> None:
        super().__init__()
        self.title("Library Management System")
        self.geometry("980x640")
        self.minsize(780, 500)
        self.configure(bg=COLOR_BG)

        self.repository = BookRepository(database_path or default_database_path())
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Status: Ready.")
        self._book_ids: list[int] = []
        self._has_placeholder = False

        self._configure_styles()
        self._build_widgets()
        self._set_placeholder()
        self._load_books()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Catalog.Treeview",
            background=COLOR_BG,
            foreground=COLOR_TEXT,
            fieldbackground=COLOR_BG,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_BORDER,
            darkcolor=COLOR_BORDER,
            rowheight=34,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Catalog.Treeview.Heading",
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            bordercolor=COLOR_BORDER,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 8),
        )
        style.map(
            "Catalog.Treeview.Heading",
            background=[("active", "#d5dee8")],
        )
        style.map(
            "Catalog.Treeview",
            background=[("selected", COLOR_ROW_SELECTED)],
            foreground=[("selected", COLOR_TEXT)],
        )

    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=COLOR_PRIMARY, height=64)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        tk.Label(
            header,
            text="Library Management System",
            bg=COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", padx=24, pady=15)

        content = tk.Frame(self, bg=COLOR_BG, padx=24, pady=20)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        navigation = tk.Frame(content, bg=COLOR_BG)
        navigation.grid(row=0, column=0, sticky="w", pady=(0, 18))

        RoundedButton(navigation, text="Books", variant="primary", padx=18, pady=7).pack(
            side="left", padx=(0, 10)
        )
        for tab_label in ("Members (later)", "Loans (later)", "Reports (later)"):
            RoundedButton(
                navigation, text=tab_label, variant="muted", state="disabled", padx=14, pady=7
            ).pack(side="left", padx=(0, 10))

        search_frame = tk.Frame(content, bg=COLOR_BG)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        search_frame.columnconfigure(1, weight=1)

        tk.Label(
            search_frame,
            text="Search",
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, padx=(0, 14))

        search_box = RoundedEntry(search_frame, textvariable=self.search_var, height=36)
        search_box.grid(row=0, column=1, sticky="ew")
        self.search_entry = search_box.entry
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in, add="+")
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out, add="+")
        self.search_entry.bind("<Return>", lambda _event: self._search())

        RoundedButton(
            search_frame, text="Search", command=self._search, variant="primary", padx=20, pady=7
        ).grid(row=0, column=2, padx=(12, 8))

        RoundedButton(
            search_frame, text="Clear", command=self._clear_search, variant="secondary", padx=18, pady=7
        ).grid(row=0, column=3)

        table_border = tk.Frame(content, bg=COLOR_BORDER, padx=1, pady=1)
        table_border.grid(row=2, column=0, sticky="nsew")
        table_border.columnconfigure(0, weight=1)
        table_border.rowconfigure(0, weight=1)

        columns = ("id", "title", "author", "isbn", "category")
        self.book_table = ttk.Treeview(
            table_border,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Catalog.Treeview",
        )
        headings = {
            "id": "ID",
            "title": "Title",
            "author": "Author",
            "isbn": "ISBN",
            "category": "Category",
        }
        widths = {"id": 65, "title": 270, "author": 220, "isbn": 165, "category": 170}
        for column in columns:
            self.book_table.heading(column, text=headings[column], anchor="w")
            self.book_table.column(column, width=widths[column], anchor="w")

        self.book_table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            table_border, orient="vertical", command=self.book_table.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.book_table.configure(yscrollcommand=scrollbar.set)
        self.book_table.bind("<Double-1>", self._on_table_double_click)

        self.empty_label = tk.Label(
            content,
            text="",
            bg=COLOR_BG,
            fg=COLOR_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.empty_label.grid(row=3, column=0, sticky="w", pady=(8, 0))

        actions = tk.Frame(content, bg=COLOR_BG)
        actions.grid(row=4, column=0, sticky="w", pady=(14, 0))

        RoundedButton(
            actions, text="Add", command=self._add_book, variant="primary", padx=20, pady=7
        ).pack(side="left", padx=(0, 10))

        RoundedButton(
            actions, text="Edit", command=self._edit_book, variant="secondary", padx=20, pady=7
        ).pack(side="left", padx=(0, 10))

        RoundedButton(
            actions, text="Delete", command=self._delete_book, variant="danger", padx=18, pady=7
        ).pack(side="left")

        status_bar = tk.Frame(self, bg=COLOR_SURFACE, height=36)
        status_bar.grid(row=2, column=0, sticky="ew")
        status_bar.grid_propagate(False)
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="both", expand=True, padx=24, pady=8)

    def _set_placeholder(self) -> None:
        self._has_placeholder = True
        self.search_entry.configure(fg=COLOR_MUTED)
        self.search_var.set(self.SEARCH_PLACEHOLDER)

    def _on_search_focus_in(self, _event=None) -> None:
        if self._has_placeholder:
            self._has_placeholder = False
            self.search_var.set("")
            self.search_entry.configure(fg=COLOR_TEXT)

    def _on_search_focus_out(self, _event=None) -> None:
        if not self.search_var.get().strip():
            self._set_placeholder()

    def _get_search_query(self) -> str:
        raw = self.search_var.get()
        if self._has_placeholder and raw == self.SEARCH_PLACEHOLDER:
            return ""
        return raw

    def _set_status(self, message: str) -> None:
        self.status_var.set(f"Status: {message}")

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
            self.empty_label.configure(text="")
            self._set_status(f"{len(books)} book(s) shown.")
        else:
            self.empty_label.configure(text="No books found.")
            self._set_status("No books found.")

    def _search(self) -> None:
        self._load_books(self._get_search_query())

    def _clear_search(self) -> None:
        if self.focus_get() == self.search_entry:
            self._has_placeholder = False
            self.search_var.set("")
            self.search_entry.configure(fg=COLOR_TEXT)
        else:
            self._set_placeholder()
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

    def _on_table_double_click(self, event: tk.Event) -> None:
        region = self.book_table.identify_region(event.x, event.y)
        row_id = self.book_table.identify_row(event.y)
        if region == "cell" and row_id:
            self._edit_book()

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
            self._load_books(self._get_search_query())
            self._set_status("Book saved successfully.")
        elif self.repository.update_book(book_id, title, author, isbn, category):
            self._load_books(self._get_search_query())
            self._set_status("Book updated successfully.")
        else:
            raise ValueError("The selected book no longer exists.")

    def _delete_book(self) -> None:
        book = self._selected_book()
        if not book:
            return
        dialog = ConfirmDeleteDialog(self)
        self.wait_window(dialog)
        if not dialog.confirmed:
            return
        if self.repository.delete_book(book.id):
            self._load_books(self._get_search_query())
            self._set_status("Book deleted successfully.")
        else:
            messagebox.showerror("Delete failed", "The book could not be deleted.", parent=self)


def main() -> None:
    """Start the desktop application."""
    app = LibraryApplication()
    app.mainloop()


if __name__ == "__main__":
    main()
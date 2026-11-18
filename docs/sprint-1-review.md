## 1. Sprint 1 Overview (Weeks 10–11)

* **Sprint Goal:** Confirm the project requirements and deliver a working app shell with a searchable book catalog.
* **Duration:** 10 working days (from **W10-D1** to **W11-D5**).
* **Task 1.7 Acceptance Criteria:** Book catalog demonstrated; feedback recorded.

### Work Breakdown Structure (WBS) Summary

| WBS | Task Name | Feature Type | Responsible | Timeline | Status | Deliverable / Acceptance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1.1** | Confirm requirements and acceptance checks | Analysis | Vũ Anh Đức | W10-D1 | Done | Feature list and simple checks agreed |
| **1.2** | Sketch screens and navigation (UI/UX) | UX | Lê Việt Đức | W10-D2 | Done | Screen flow for main pages |
| **1.3** | Design database tables and app structure | Architecture / DB | Đinh Mạnh Đức | W10-D3 | Done | SQLite tables and app modules outlined |
| **1.4** | Set up Tkinter window and SQLite database | Implementation | Nguyễn Minh Tuấn | W10-D4 | Done | App opens and can save sample data |
| **1.5** | Build book add, edit, delete, and search | Implementation | Đinh Mạnh Đức | W10-D5 – W11-D2 | Done | Book records can be searched and updated |
| **1.6** | Integrate and test book workflows | Testing | Phạm Hữu Hiệu | W11-D3 – W11-D4 | Done | Book changes save and display correctly |
| **1.7** | Sprint review and update backlog | Review | Võ Sỹ Thái Hào | W11-D5 | Done | Book catalog demonstrated; feedback recorded |

---

## 2. Demo & Integration Testing Results (Sprint Deliverables)

The team completed and demonstrated all three Sprint 1 deliverables:

1. **Requirements, UI/UX Design, and Database Schema:** Finalized the feature specification, UI/UX wireframes for the main catalog screen and confirmation dialog, and the SQLite `books` table schema.
2. **Desktop Book Catalog Application:**
   * **Add Book (`Add`):** Opens a modal form for `Title *`, `Author *`, `ISBN`, and `Category`; validates required fields to prevent saving incomplete records; immediately updates the catalog table; and displays `Status: Book saved successfully.`.
   * **Search (`Search` & `Clear`):** Filters records case-insensitively by title, author, ISBN, or category; displays `"No books found."` below the table when no records match; and restores the full catalog when clicking `Clear`.
   * **Edit Book (`Edit`):** Updates an existing record either by selecting a row and clicking `Edit` or by double-clicking a book row.
   * **Delete Book (`Delete`):** Displays a custom `Confirm delete` dialog (*"Delete this book? This cannot be undone."*) before permanently removing the record from both the UI and SQLite.
   * **Data Persistence:** All book additions, edits, and deletions persist across application restarts in the SQLite database.
3. **Defects Resolved During Integration Testing (Task 1.6):**
   * **UI Alignment with Wireframes:** Standardized the primary blue theme (`#2f6091`), rounded action buttons, seamless search input with placeholder text, and redesigned the `Confirm delete` dialog to match the initial UI/UX sketches.
   * **Fixed ID Sorting Order:** Updated the SQL query to sort by `ORDER BY id ASC` instead of alphabetical title ordering, resolving the issue where records appeared out of numeric sequence (e.g., `1, 10, 2, 3`).
   * **Fixed Table Header Double-Click Bug:** Restricted the `<Double-1>` event handler to trigger only when double-clicking actual data cells (`region == "cell"`), preventing accidental `Edit` dialogs when double-clicking column headers (`ID`, `Title`, `Author`, `ISBN`, `Category`).

---

## 3. Sprint Review Feedback

| Category | Feedback / Observations |
| :--- | :--- | :--- |
| **UI / UX** | Clean layout with distinct color-coded action buttons (`Add`, `Edit`, `Delete`) matching the initial wireframes. | 
| **Workflows** | CRUD and search operations respond quickly, and the bottom status bar (`Status: ...`) provides clear user feedback. |
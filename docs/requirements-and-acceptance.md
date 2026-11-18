# Sprint 1: Requirements and acceptance checks

**Project:** Library Management System  
**Sprint:** 1 (Weeks 10–11)  
**Owner:** Vũ Anh Đức (WBS 1.1)  
**Task deliverable:** Feature list and simple acceptance checks  
**Status:** Baseline prepared from the project plan; confirm open decisions with the group before treating them as agreed.

## Product requirements

The application is a Windows desktop tool for a librarian. It uses Python/Tkinter and a local SQLite database. The complete project scope includes book and member management, checkout and return, loan status and reports, and CSV export of loan history.

### Sprint 1 book-catalog increment

1. The librarian can create a book record.
2. The librarian can view the catalog and select a record to edit or delete.
3. The librarian can search the catalog and see matching books.
4. Book changes are stored locally in SQLite and remain available after the application is closed and reopened.
5. The app provides clear feedback when an operation succeeds or cannot be completed because the input is invalid.

Member and loan workflows, reports, and CSV export are in the overall project scope, but are scheduled for later sprints in the supplied plan.

## Acceptance checks

These are observable, implementation-independent checks for the Sprint 1 book catalog.

| ID | Given / When | Then |
|---|---|---|
| AC-01 Create | The app is open and the librarian enters valid book details and saves. | A new book appears in the catalog with the entered details. |
| AC-02 Required input | The librarian attempts to save a book with a required value missing or whitespace-only. | The app explains the input problem and does not create an incomplete record. |
| AC-03 Edit | A saved book is selected, changed, and saved. | The catalog shows the updated values; no duplicate record is created by the edit. |
| AC-04 Delete | A saved book is selected and the librarian confirms deletion. | The book no longer appears in the catalog or search results. |
| AC-05 Search match | The librarian searches for text present in a book's searchable details. | Matching book records are shown. |
| AC-06 Search no match | The librarian searches for text not present in any book. | No unrelated book is shown and the empty result is clear. |
| AC-07 Persistence | A book is created or edited, then the app is closed and reopened. | The saved state is still present. |
| AC-08 Safe delete | The librarian initiates deletion and cancels the confirmation. | The book remains in the catalog. |

## Open decisions for group confirmation

The supplied plan does not define the book fields, which fields are required, whether ISBN must be unique, or which fields search covers. Agree these before database/UI implementation. A reasonable starting proposal is title and author as required fields, with ISBN and category optional; search title, author, ISBN, and category without case sensitivity. This proposal is not yet a group decision.

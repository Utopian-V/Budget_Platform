# Client Action Items -- Budget Platform

This document lists every feature, button, or UI element that currently operates
without a real backend integration or requires client-provided credentials/data
to become fully functional.

---

## 1. Google SSO Authentication

**Where it appears:** Settings page (Authentication section), Header profile dropdown (Sign Out button)

**Current behavior:** Displays "Pending Setup" badge. Sign Out button is non-functional. All pages are accessible without login.

**What is needed from client:**
- Google Cloud Console project with OAuth 2.0 credentials
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` values
- Authorized redirect URI configuration
- List of allowed email domains (if restricting to a workspace)

---

## 2. Zoho Books API Integration

**Where it appears:** Settings page (Zoho Integration section)

**Current behavior:** Displays "Pending Setup" badge. Backend has a stub `zoho_service.py` ready to accept credentials.

**What is needed from client:**
- Zoho Books organization ID (`ZOHO_ORG_ID`)
- Zoho API OAuth client ID (`ZOHO_CLIENT_ID`)
- Zoho API OAuth client secret (`ZOHO_CLIENT_SECRET`)
- Initial refresh token generated via Zoho's OAuth consent flow
- Confirmation of which Zoho Books modules to sync (Invoices, Sales Orders, Credit Notes, Quotations)

---

## 3. Header Global Search

**Where it appears:** Header search bar (top right, visible on desktop)

**Current behavior:** Accepts text input but does not search anything. It is a visual placeholder.

**What is needed from client:**
- Confirmation of what entities to search across (clients, invoices, budget lines, proposals?)
- Priority: whether to implement this as a global search or remove it from the header

---

## 4. True-Up "Mark Resolved" Persistence

**Where it appears:** True-Up Review page, "Mark Resolved" / "Resolved" toggle buttons

**Current behavior:** Toggling resolved/unresolved state is session-only (stored in React state). Refreshing the page resets all items to unresolved.

**What is needed from client:**
- Confirmation that true-up resolution should be persisted to the database
- Whether resolved items need an associated remark/note
- Whether resolved items should be excluded from future true-up candidate lists

---

## 5. Reconciliation "Promote" Action

**Where it appears:** Reconciliation page, "Promote" button next to each new addition

**Current behavior:** Calls `POST /api/budget/promote` which creates a Level 2 budget line. Works correctly but extracts client name from the discrepancy detail text, which may not be ideal.

**What is needed from client:**
- Confirmation of what fields should populate the new budget line (client name, department, manager, billing entity)
- Whether promotion should trigger a notification to the relevant manager
- Whether promoted items should be removed from the new-additions list

---

## 6. Settings Import Buttons

**Where it appears:** Settings page, per-data-type "Import" buttons (Budget, Invoices, Sales Orders, Credit Notes, Proposals)

**Current behavior:** Reads from Excel files on the server filesystem at fixed paths. Works when files exist at the expected locations.

**What is needed from client:**
- Confirmation of file naming conventions if they change year-to-year
- Whether file upload from the browser should replace the current fixed-path approach
- Updated Excel files whenever new data needs to be imported

---

## 7. Manager Notification System

**Where it appears:** Not yet built

**Current behavior:** Does not exist. The original project requirements mention manager notifications for variance thresholds.

**What is needed from client:**
- Preferred notification channel (email, in-app alerts, or both)
- Variance threshold that should trigger a notification
- List of managers and their email addresses (if email)
- Whether notifications should be per-month or per-reconciliation-run

---

## 8. Profile Settings

**Where it appears:** Header profile dropdown, "Profile Settings" button

**Current behavior:** Button exists but does nothing (no page or modal wired to it).

**What is needed from client:**
- Whether user profiles are needed before Google SSO is configured
- What profile fields should be editable (name, notification preferences, role)

---

## 9. Filter Dropdowns (Status Values)

**Where it appears:** Invoices page (status filter), Sales Orders page (status filter), Proposals page (status filter)

**Current behavior:** Filter dropdown options are hardcoded in the frontend (e.g., "Paid", "Void", "Draft", "Overdue"). They do not come from the API or the actual data.

**What is needed from client:**
- Canonical list of all possible statuses for each entity in Zoho Books
- Whether new statuses can appear over time (requiring dynamic loading)

---

## 10. Deployment Configuration

**Where it appears:** N/A (infrastructure)

**Current behavior:** Runs locally with SQLite.

**What is needed from client:**
- Target deployment environment (AWS, GCP, Azure, on-premises)
- Whether PostgreSQL should replace SQLite
- Domain name for the application
- SSL certificate requirements
- Expected number of concurrent users

---

## Summary Table

| # | Item | Blocking? | Client Action |
|---|------|-----------|---------------|
| 1 | Google SSO | No (app works without auth) | Provide OAuth credentials |
| 2 | Zoho Books | No (manual import works) | Provide API credentials |
| 3 | Global Search | No (cosmetic) | Confirm scope or remove |
| 4 | True-Up Persistence | Minor | Confirm DB storage needs |
| 5 | Promote Details | Minor | Confirm field mapping |
| 6 | File Upload | No (server files work) | Decide on uploaddis UX |
| 7 | Notifications | Missing feature | Define channel + thresholds |
| 8 | Profile Settings | No | Depends on SSO |
| 9 | Status Filters | Minor | Provide canonical lists |
| 10 | Deployment | When ready | Provide infra details |

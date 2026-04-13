# Frontend Audit -- Recommended Improvements

## Critical Issues (Fixed in This Session)

1. **Data contract mismatches** -- All five data pages (Budget, Invoices, Sales Orders, Proposals, Reports) used field names that didn't match the backend API responses. Every page was reading `res.data` instead of `res.data.data` for paginated endpoints. **Status: Fixed.**

2. **Number truncation** -- StatCard values used CSS `truncate` which clipped large currency numbers with ellipsis. **Status: Fixed** (replaced with `break-all`).

3. **Hardcoded user identity** -- "Vansh Kapoor" / "VP" was hardcoded in Sidebar and Header. **Status: Fixed** (replaced with generic "Admin").

4. **Missing route title** -- Header `routeTitles` map didn't include `/true-up`. **Status: Fixed.**

5. **Export bug** -- Client Summary tab exported reconciliation data instead. **Status: Fixed** (added proper `client-summary` export type).

6. **Backend `HTTPException` import missing** in `reports.py` export endpoint. **Status: Fixed.**

---

## UX Improvements -- Recommended

### P1: High Impact

#### 1. Variance Color Convention Inconsistency
- **Dashboard** department table: positive variance = red, negative = green
- **Budget** page and **Reports** page: positive variance = green, negative = red
- **Recommendation:** Standardize. In accounting, "budget minus actual" being positive means under-spend (good), so positive = green is correct. Fix Dashboard to match.

#### 2. Empty State Messaging
- When no data is imported, pages show "No data" or empty tables with no guidance.
- **Recommendation:** Add a call-to-action on empty states: "No data yet. Go to Settings to import your Excel files." with a link to `/settings`.

#### 3. Error Feedback
- All `catch` blocks silently swallow errors. Users get no feedback when an API call fails.
- **Recommendation:** Add a lightweight toast notification system. Show "Import failed" / "Reconciliation error" / "Export failed" messages when API calls fail.

#### 4. Loading States on Buttons
- Import buttons, Reconciliation "Run" button, and Export button show spinners, which is good.
- **Recommendation:** Also add loading states to the Promote and Snapshot buttons after they fire, with a success confirmation (e.g., brief green flash or checkmark).

#### 5. Pagination is Client-Side Only
- DataTable paginates the data array it receives, but the backend only sends 50 rows per request (default limit).
- **Recommendation:** Either increase the backend default limit to 500 for list endpoints, or implement server-side pagination with "Load More" / page controls that call the API with `skip` and `limit`.

### P2: Medium Impact

#### 6. Mobile Responsiveness
- The sidebar collapses properly on mobile, but the data tables overflow horizontally.
- **Recommendation:** For tables with many columns (Budget monthly breakdown, MTD/YTD), add horizontal scroll indicators or a "swipe to see more" hint on mobile.

#### 7. Filter Persistence
- When navigating between pages and back, all filters reset to defaults.
- **Recommendation:** Use URL search params (`?month=Apr-25&department=Tax`) so filters survive navigation and are shareable via URL.

#### 8. Dashboard Recent Activity
- Shows 20 mixed items (invoices + proposals) sorted by date, but no way to filter or see more.
- **Recommendation:** Add a "View All" link to the relevant page. Add type tabs (All / Invoices / Proposals).

#### 9. Search Bar in Header
- The header search bar accepts input but does nothing.
- **Recommendation:** Either implement global search across all entities or remove the search bar to avoid confusion.

#### 10. Bulk Actions
- No ability to select multiple rows and act on them (e.g., bulk promote new additions, bulk mark resolved).
- **Recommendation:** Add checkbox column to DataTable with bulk action bar.

### P3: Nice to Have

#### 11. Dark Mode
- CSS variables exist (`--color-sidebar`, `--color-sidebar-hover`) suggesting preparation for theming.
- **Recommendation:** Add a dark mode toggle in Settings or the profile dropdown.

#### 12. Keyboard Shortcuts
- No keyboard navigation or shortcuts exist.
- **Recommendation:** Add `Ctrl+K` for search, `Escape` to close modals/dropdowns, arrow keys for table navigation.

#### 13. Data Refresh Indicator
- No indication of when data was last imported or when reconciliation was last run.
- **Recommendation:** Show "Last imported: 3 hours ago" on the Dashboard or Settings page.

#### 14. Reconciliation History Timeline
- Snapshots exist but aren't displayed anywhere in the UI.
- **Recommendation:** Add a "History" section to the Reconciliation page showing past snapshots with the ability to compare two snapshots side by side.

#### 15. Chart Interactivity
- Dashboard and Reports charts are basic line/bar charts.
- **Recommendation:** Add click-to-drill-down on chart elements (e.g., click a department bar to navigate to its filtered budget view).

---

## Accessibility Issues

1. **Color contrast** -- Some text uses `text-slate-400` / `text-slate-500` on white backgrounds, which may not meet WCAG AA contrast ratios.
2. **Focus indicators** -- Buttons use `focus:ring-2` which is good. Table rows and filter dropdowns should also have visible focus indicators.
3. **Screen reader labels** -- Icon-only buttons (mobile menu toggle, pagination arrows) lack `aria-label` attributes.
4. **Skip navigation** -- No "skip to main content" link for keyboard users.

---

## Performance Considerations

1. **Bundle size** -- Recharts is a large dependency. Consider lazy-loading chart components with `React.lazy()` since not every page needs charts.
2. **API waterfall** -- Dashboard makes 3 parallel API calls, which is good. But the Reconciliation page makes 3 serial calls inside `Promise.all`, and the Budget page makes an additional master data call on mount. Consider batching or caching.
3. **Re-renders** -- The Budget page re-renders the entire column definition array on every `expandedId` change due to the `useMemo` dependency. Extract the expand cell into a separate component to avoid this.

---

## File Structure Recommendation

Current structure is flat:
```
src/
  pages/       (9 files)
  components/  (4 files)
  lib/         (2 files)
```

As the app grows, consider:
```
src/
  features/
    dashboard/
    budget/
    reconciliation/
    ...
  shared/
    components/
    hooks/
    utils/
  api/
```

This keeps feature-specific components, hooks, and types co-located.

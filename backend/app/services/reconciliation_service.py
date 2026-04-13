"""
Automated reconciliation engine for the Budget Platform.

Replaces manual VLOOKUP/INDEX-MATCH reconciliation work by linking budget lines
to invoices via a unique code ({Sales Order Number}{Service Category}), detecting
unmatched items, flagging new additions, filtering OOP expenses, computing
variances, and applying credit note adjustments.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    BudgetLevel,
    BudgetLine,
    BudgetMonthly,
    CreditNote,
    Invoice,
    ReconciliationRecord,
    SalesOrder,
)

logger = logging.getLogger(__name__)

# Financial year months in order (Indian FY: Apr → Mar)
FY_MONTHS = [
    "Apr", "May", "Jun", "Jul", "Aug", "Sep",
    "Oct", "Nov", "Dec", "Jan", "Feb", "Mar",
]

OOP_KEYWORDS = [
    "reimbursement", "out of pocket", "oop",
    "travel", "conveyance", "lodging", "boarding",
    "per diem", "airfare", "hotel",
]

PREVIOUS_YEAR_PATTERNS = re.compile(
    r"20(?:1[0-9]|2[0-4])-(?:1[0-9]|2[0-5])"  # matches 2010-11 … 2024-25
)

CURRENT_YEAR_PATTERN = re.compile(r"2025-26")


# ──────────────────────────────────────────────
# Data classes for structured return values
# ──────────────────────────────────────────────

@dataclass
class UnmatchedItem:
    invoice_id: int
    invoice_number: Optional[str]
    unique_code: Optional[str]
    sales_order_number: Optional[str]
    item_name: Optional[str]
    item_total: float
    category: str  # direct_invoice | previous_year_so | service_category_mismatch | line_item_mismatch | split_invoice | unknown
    detail: str = ""


@dataclass
class NewAddition:
    invoice_id: int
    invoice_number: Optional[str]
    unique_code: Optional[str]
    sales_order_number: Optional[str]
    customer_name: Optional[str]
    item_name: Optional[str]
    item_total: float
    service_category: Optional[str] = None


@dataclass
class VarianceResult:
    budget_line_id: int
    month: str
    expected: float
    actual: float
    mtd_variance: float
    ytd_variance: float


@dataclass
class ReconciliationSummary:
    month: str
    total_budget_amount: float = 0.0
    total_invoice_amount: float = 0.0
    matched_amount: float = 0.0
    unmatched_amount: float = 0.0
    unmatched_by_category: dict = field(default_factory=dict)
    oop_amount: float = 0.0
    credit_note_adjustment: float = 0.0
    new_addition_count: int = 0
    matched_count: int = 0
    unmatched_count: int = 0


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _month_index(month: str) -> int:
    """Convert 'Apr-25' → 0, 'May-25' → 1, … 'Mar-26' → 11."""
    abbr = month.split("-")[0]
    try:
        return FY_MONTHS.index(abbr)
    except ValueError:
        logger.warning("Unrecognised month abbreviation: %s", month)
        return -1


def _is_oop(item_name: Optional[str]) -> bool:
    if not item_name:
        return False
    lower = item_name.lower()
    return any(kw in lower for kw in OOP_KEYWORDS)


def _is_previous_year_so(so_number: Optional[str]) -> bool:
    if not so_number:
        return False
    return bool(PREVIOUS_YEAR_PATTERNS.search(so_number))


def _extract_so_base(so_number: Optional[str]) -> Optional[str]:
    """Strip trailing sequence digits to get the base SO identifier."""
    if not so_number:
        return None
    return so_number.strip()


def _get_active_invoices(db: Session, month: str) -> list[Invoice]:
    """Return non-voided invoice rows for a given month."""
    return (
        db.query(Invoice)
        .filter(
            Invoice.invoice_month == month,
            Invoice.is_voided == False,  # noqa: E712
        )
        .all()
    )


def _build_budget_code_map(db: Session) -> dict[str, list[BudgetLine]]:
    """Map unique_code_invoice → list of BudgetLine rows."""
    lines = (
        db.query(BudgetLine)
        .filter(BudgetLine.unique_code_invoice.isnot(None))
        .all()
    )
    code_map: dict[str, list[BudgetLine]] = defaultdict(list)
    for bl in lines:
        code_map[bl.unique_code_invoice].append(bl)
    return code_map


def _build_so_set(db: Session) -> set[str]:
    """Set of all sales order numbers present in budget lines."""
    rows = (
        db.query(BudgetLine.sales_order_no)
        .filter(BudgetLine.sales_order_no.isnot(None))
        .distinct()
        .all()
    )
    return {r[0].strip() for r in rows if r[0]}


def _build_so_service_map(db: Session) -> dict[str, set[str]]:
    """SO number → set of service categories from budget lines."""
    rows = (
        db.query(BudgetLine.sales_order_no, BudgetLine.service_category)
        .filter(
            BudgetLine.sales_order_no.isnot(None),
            BudgetLine.service_category.isnot(None),
        )
        .all()
    )
    mapping: dict[str, set[str]] = defaultdict(set)
    for so, sc in rows:
        mapping[so.strip()].add(sc.strip())
    return mapping


def _build_so_item_counts(db: Session) -> dict[str, int]:
    """SO number → count of line items in budget."""
    rows = (
        db.query(BudgetLine.sales_order_no, func.count(BudgetLine.id))
        .filter(BudgetLine.sales_order_no.isnot(None))
        .group_by(BudgetLine.sales_order_no)
        .all()
    )
    return {so.strip(): cnt for so, cnt in rows if so}


def _build_invoice_counts_per_so(invoices: list[Invoice]) -> dict[str, set[str]]:
    """SO number → set of distinct service-categories seen across invoices."""
    mapping: dict[str, set[str]] = defaultdict(set)
    for inv in invoices:
        if inv.sales_order_number and inv.item_name:
            mapping[inv.sales_order_number.strip()].add(inv.item_name.strip())
    return mapping


# ──────────────────────────────────────────────
# Step 1: Auto-Match
# ──────────────────────────────────────────────

def _auto_match(
    db: Session,
    month: str,
    invoices: list[Invoice],
    budget_code_map: dict[str, list[BudgetLine]],
) -> tuple[list[Invoice], list[Invoice]]:
    """
    Match invoices to budget lines via unique_code.
    Returns (matched_invoices, unmatched_invoices).
    """
    matched: list[Invoice] = []
    unmatched: list[Invoice] = []

    for inv in invoices:
        if not inv.unique_code:
            unmatched.append(inv)
            continue
        budget_lines = budget_code_map.get(inv.unique_code)
        if budget_lines:
            matched.append(inv)
        else:
            unmatched.append(inv)

    logger.info(
        "Month %s auto-match: %d matched, %d unmatched out of %d invoices",
        month, len(matched), len(unmatched), len(invoices),
    )
    return matched, unmatched


# ──────────────────────────────────────────────
# Step 2: Categorise unmatched (#N/A) items
# ──────────────────────────────────────────────

def _categorise_unmatched(
    unmatched_invoices: list[Invoice],
    budget_so_set: set[str],
    so_service_map: dict[str, set[str]],
    so_item_counts: dict[str, int],
    invoice_so_categories: dict[str, set[str]],
) -> list[UnmatchedItem]:
    results: list[UnmatchedItem] = []

    for inv in unmatched_invoices:
        so = _extract_so_base(inv.sales_order_number)

        # 1. No sales order at all → direct invoice
        if not so:
            results.append(UnmatchedItem(
                invoice_id=inv.id,
                invoice_number=inv.invoice_number,
                unique_code=inv.unique_code,
                sales_order_number=inv.sales_order_number,
                item_name=inv.item_name,
                item_total=inv.cleaned_item_total or 0,
                category="direct_invoice",
                detail="Invoice raised without a Sales Order",
            ))
            continue

        # 2. Previous-year SO
        if _is_previous_year_so(so):
            results.append(UnmatchedItem(
                invoice_id=inv.id,
                invoice_number=inv.invoice_number,
                unique_code=inv.unique_code,
                sales_order_number=so,
                item_name=inv.item_name,
                item_total=inv.cleaned_item_total or 0,
                category="previous_year_so",
                detail=f"SO belongs to a previous financial year: {so}",
            ))
            continue

        # 3–5: SO exists in budget?
        if so in budget_so_set:
            budget_cats = so_service_map.get(so, set())
            inv_cats = invoice_so_categories.get(so, set())

            # 5. Split invoice: multiple distinct service categories on same SO
            if len(inv_cats) > 1:
                results.append(UnmatchedItem(
                    invoice_id=inv.id,
                    invoice_number=inv.invoice_number,
                    unique_code=inv.unique_code,
                    sales_order_number=so,
                    item_name=inv.item_name,
                    item_total=inv.cleaned_item_total or 0,
                    category="split_invoice",
                    detail=f"Multiple service categories on SO: {', '.join(inv_cats)}",
                ))
                continue

            # 3. Service category mismatch
            inv_item = (inv.item_name or "").strip()
            if inv_item and budget_cats and inv_item not in budget_cats:
                results.append(UnmatchedItem(
                    invoice_id=inv.id,
                    invoice_number=inv.invoice_number,
                    unique_code=inv.unique_code,
                    sales_order_number=so,
                    item_name=inv.item_name,
                    item_total=inv.cleaned_item_total or 0,
                    category="service_category_mismatch",
                    detail=(
                        f"Invoice category '{inv_item}' not in budget categories "
                        f"for SO: {budget_cats}"
                    ),
                ))
                continue

            # 4. Line item count mismatch
            budget_count = so_item_counts.get(so, 0)
            inv_count = len(inv_cats)
            if inv_count > budget_count:
                results.append(UnmatchedItem(
                    invoice_id=inv.id,
                    invoice_number=inv.invoice_number,
                    unique_code=inv.unique_code,
                    sales_order_number=so,
                    item_name=inv.item_name,
                    item_total=inv.cleaned_item_total or 0,
                    category="line_item_mismatch",
                    detail=(
                        f"Invoice has {inv_count} items vs {budget_count} budget lines for SO"
                    ),
                ))
                continue

        # 6. Catch-all
        results.append(UnmatchedItem(
            invoice_id=inv.id,
            invoice_number=inv.invoice_number,
            unique_code=inv.unique_code,
            sales_order_number=so,
            item_name=inv.item_name,
            item_total=inv.cleaned_item_total or 0,
            category="unknown",
            detail="Could not auto-categorise the mismatch",
        ))

    return results


# ──────────────────────────────────────────────
# Step 3: New Additions detection
# ──────────────────────────────────────────────

def _detect_new_additions(
    db: Session,
    unmatched_invoices: list[Invoice],
    budget_so_set: set[str],
) -> list[NewAddition]:
    """
    Invoices whose SO is valid and current-year but not in the original budget
    are candidates for Level 2 (New Addition) budget lines.
    """
    additions: list[NewAddition] = []

    for inv in unmatched_invoices:
        so = _extract_so_base(inv.sales_order_number)
        if not so:
            continue
        if _is_previous_year_so(so):
            continue
        if _is_oop(inv.item_name):
            continue
        if so in budget_so_set:
            continue

        # Valid SO not in budget → new addition
        so_record = (
            db.query(SalesOrder)
            .filter(SalesOrder.salesorder_number == so)
            .first()
        )

        additions.append(NewAddition(
            invoice_id=inv.id,
            invoice_number=inv.invoice_number,
            unique_code=inv.unique_code,
            sales_order_number=so,
            customer_name=inv.customer_name,
            item_name=inv.item_name,
            item_total=inv.cleaned_item_total or 0,
            service_category=so_record.item_name if so_record else inv.item_name,
        ))

    logger.info("Detected %d new-addition candidates", len(additions))
    return additions


# ──────────────────────────────────────────────
# Step 4: OOP Filtering
# ──────────────────────────────────────────────

def _filter_oop(invoices: list[Invoice]) -> tuple[list[Invoice], list[Invoice]]:
    """Split invoices into (non-OOP, OOP)."""
    oop: list[Invoice] = []
    non_oop: list[Invoice] = []
    for inv in invoices:
        if _is_oop(inv.item_name):
            oop.append(inv)
        else:
            non_oop.append(inv)
    return non_oop, oop


# ──────────────────────────────────────────────
# Step 5: Variance Calculation
# ──────────────────────────────────────────────

def calculate_variances(db: Session, month: str) -> list[VarianceResult]:
    """
    For each budget line with a BudgetMonthly record for *month*:
      MTD = expected − actual
      YTD = Σ(expected − actual) for all months up to and including *month*
    Writes results back to the BudgetMonthly rows.
    """
    target_idx = _month_index(month)
    if target_idx < 0:
        logger.error("Invalid month for variance calc: %s", month)
        return []

    monthly_rows = (
        db.query(BudgetMonthly)
        .filter(BudgetMonthly.month == month)
        .all()
    )

    results: list[VarianceResult] = []
    for row in monthly_rows:
        mtd = (row.expected or 0) - (row.actual or 0)
        row.mtd_variance = mtd

        # YTD: sum variances for all months with index ≤ target_idx
        ytd_rows = (
            db.query(
                func.coalesce(func.sum(BudgetMonthly.expected), 0),
                func.coalesce(func.sum(BudgetMonthly.actual), 0),
            )
            .filter(
                BudgetMonthly.budget_line_id == row.budget_line_id,
                BudgetMonthly.month_index <= target_idx,
            )
            .one()
        )
        ytd = ytd_rows[0] - ytd_rows[1]
        row.ytd_variance = ytd

        results.append(VarianceResult(
            budget_line_id=row.budget_line_id,
            month=month,
            expected=row.expected or 0,
            actual=row.actual or 0,
            mtd_variance=mtd,
            ytd_variance=ytd,
        ))

    db.flush()
    logger.info("Calculated variances for %d budget lines in %s", len(results), month)
    return results


# ──────────────────────────────────────────────
# Step 6: Credit Note Adjustments
# ──────────────────────────────────────────────

def _apply_credit_notes(
    db: Session,
    month: str,
    budget_code_map: dict[str, list[BudgetLine]],
) -> float:
    """
    Credit notes offset invoice amounts. Walk the chain:
        CreditNote.associated_invoice_number → Invoice → unique_code → BudgetLine
    Returns total credit note adjustment applied.
    """
    credit_notes = db.query(CreditNote).filter(
        CreditNote.item_total_adjusted.isnot(None),
    ).all()

    total_adjustment = 0.0

    for cn in credit_notes:
        if not cn.associated_invoice_number:
            continue

        linked_invoice = (
            db.query(Invoice)
            .filter(
                Invoice.invoice_number == cn.associated_invoice_number,
                Invoice.invoice_month == month,
            )
            .first()
        )
        if not linked_invoice or not linked_invoice.unique_code:
            continue

        budget_lines = budget_code_map.get(linked_invoice.unique_code, [])
        if not budget_lines:
            continue

        adjustment = cn.item_total_adjusted or 0  # already negative
        total_adjustment += adjustment

        # Apply the adjustment to the first matching BudgetMonthly actual
        monthly = (
            db.query(BudgetMonthly)
            .filter(
                BudgetMonthly.budget_line_id == budget_lines[0].id,
                BudgetMonthly.month == month,
            )
            .first()
        )
        if monthly:
            monthly.actual = (monthly.actual or 0) + adjustment
            logger.debug(
                "Credit note %s adjusted budget line %d month %s by %.2f",
                cn.cn_number, budget_lines[0].id, month, adjustment,
            )

    db.flush()
    logger.info("Applied credit note adjustments for %s: total %.2f", month, total_adjustment)
    return total_adjustment


# ──────────────────────────────────────────────
# Step 7: Reconciliation Summary
# ──────────────────────────────────────────────

def get_reconciliation_summary(db: Session, month: str) -> ReconciliationSummary:
    """Build a reconciliation summary for a single month."""
    invoices = _get_active_invoices(db, month)
    budget_code_map = _build_budget_code_map(db)

    matched_inv, unmatched_inv = _auto_match(db, month, invoices, budget_code_map)
    non_oop_unmatched, oop_inv = _filter_oop(unmatched_inv)

    budget_so_set = _build_so_set(db)
    so_service_map = _build_so_service_map(db)
    so_item_counts = _build_so_item_counts(db)
    inv_so_cats = _build_invoice_counts_per_so(invoices)

    categorised = _categorise_unmatched(
        non_oop_unmatched, budget_so_set, so_service_map,
        so_item_counts, inv_so_cats,
    )

    # Aggregate budget expected for the month
    total_budget = (
        db.query(func.coalesce(func.sum(BudgetMonthly.expected), 0))
        .filter(BudgetMonthly.month == month)
        .scalar()
    )

    total_invoice = sum(inv.cleaned_item_total or 0 for inv in invoices)
    matched_amount = sum(inv.cleaned_item_total or 0 for inv in matched_inv)
    oop_amount = sum(inv.cleaned_item_total or 0 for inv in oop_inv)

    by_category: dict[str, float] = defaultdict(float)
    for item in categorised:
        by_category[item.category] += item.item_total
    by_category["oop"] = oop_amount

    unmatched_amount = total_invoice - matched_amount

    new_adds = _detect_new_additions(db, unmatched_inv, budget_so_set)

    return ReconciliationSummary(
        month=month,
        total_budget_amount=total_budget,
        total_invoice_amount=total_invoice,
        matched_amount=matched_amount,
        unmatched_amount=unmatched_amount,
        unmatched_by_category=dict(by_category),
        oop_amount=oop_amount,
        credit_note_adjustment=0.0,  # filled after credit note pass
        new_addition_count=len(new_adds),
        matched_count=len(matched_inv),
        unmatched_count=len(unmatched_inv),
    )


# ──────────────────────────────────────────────
# Public API: Unmatched items
# ──────────────────────────────────────────────

def get_unmatched_items(db: Session, month: str) -> list[UnmatchedItem]:
    """Return #N/A items with categorisation for a single month."""
    invoices = _get_active_invoices(db, month)
    budget_code_map = _build_budget_code_map(db)
    _, unmatched_inv = _auto_match(db, month, invoices, budget_code_map)
    non_oop, _ = _filter_oop(unmatched_inv)

    budget_so_set = _build_so_set(db)
    so_service_map = _build_so_service_map(db)
    so_item_counts = _build_so_item_counts(db)
    inv_so_cats = _build_invoice_counts_per_so(invoices)

    return _categorise_unmatched(
        non_oop, budget_so_set, so_service_map,
        so_item_counts, inv_so_cats,
    )


# ──────────────────────────────────────────────
# Public API: New Additions
# ──────────────────────────────────────────────

def get_new_additions(db: Session, month: str) -> list[NewAddition]:
    """Return invoices that should be added as Level 2 budget lines."""
    invoices = _get_active_invoices(db, month)
    budget_code_map = _build_budget_code_map(db)
    _, unmatched_inv = _auto_match(db, month, invoices, budget_code_map)
    budget_so_set = _build_so_set(db)
    return _detect_new_additions(db, unmatched_inv, budget_so_set)


# ──────────────────────────────────────────────
# Orchestrators
# ──────────────────────────────────────────────

def _persist_reconciliation_records(
    db: Session,
    month: str,
    matched_invoices: list[Invoice],
    unmatched_items: list[UnmatchedItem],
    budget_code_map: dict[str, list[BudgetLine]],
) -> None:
    """Write / overwrite ReconciliationRecord rows for the month."""
    db.query(ReconciliationRecord).filter(
        ReconciliationRecord.month == month,
    ).delete(synchronize_session="fetch")

    # Matched records
    matched_by_code: dict[str, float] = defaultdict(float)
    for inv in matched_invoices:
        matched_by_code[inv.unique_code] += inv.cleaned_item_total or 0

    for code, inv_total in matched_by_code.items():
        budget_lines = budget_code_map.get(code, [])
        bm = (
            db.query(BudgetMonthly)
            .filter(
                BudgetMonthly.budget_line_id == budget_lines[0].id,
                BudgetMonthly.month == month,
            )
            .first()
        ) if budget_lines else None

        budget_amt = bm.expected if bm else 0

        db.add(ReconciliationRecord(
            month=month,
            unique_code=code,
            budget_amount=budget_amt or 0,
            invoice_amount=inv_total,
            difference=(budget_amt or 0) - inv_total,
            is_matched=True,
        ))

    # Unmatched records
    for item in unmatched_items:
        db.add(ReconciliationRecord(
            month=month,
            unique_code=item.unique_code,
            budget_amount=0,
            invoice_amount=item.item_total,
            difference=-item.item_total,
            is_matched=False,
            discrepancy_type=item.category,
            discrepancy_detail=item.detail,
        ))

    db.flush()


def _update_actuals(
    db: Session,
    month: str,
    matched_invoices: list[Invoice],
    budget_code_map: dict[str, list[BudgetLine]],
) -> None:
    """Roll up matched invoice totals into BudgetMonthly.actual."""
    totals_by_code: dict[str, float] = defaultdict(float)
    for inv in matched_invoices:
        totals_by_code[inv.unique_code] += inv.cleaned_item_total or 0

    for code, total in totals_by_code.items():
        budget_lines = budget_code_map.get(code, [])
        for bl in budget_lines:
            monthly = (
                db.query(BudgetMonthly)
                .filter(
                    BudgetMonthly.budget_line_id == bl.id,
                    BudgetMonthly.month == month,
                )
                .first()
            )
            if monthly:
                monthly.actual = total
            else:
                monthly = BudgetMonthly(
                    budget_line_id=bl.id,
                    month=month,
                    month_index=_month_index(month),
                    actual=total,
                )
                db.add(monthly)

    db.flush()


def run_reconciliation(db: Session, month: str) -> ReconciliationSummary:
    """
    Full reconciliation pipeline for a single month.

    1. Auto-match invoices → budget lines via unique_code
    2. Categorise unmatched items
    3. Detect new additions
    4. Filter OOP
    5. Update actuals on BudgetMonthly
    6. Apply credit notes
    7. Calculate variances
    8. Persist reconciliation records
    9. Return summary
    """
    logger.info("── Starting reconciliation for %s ──", month)

    invoices = _get_active_invoices(db, month)
    if not invoices:
        logger.warning("No active invoices found for %s", month)
        return ReconciliationSummary(month=month)

    budget_code_map = _build_budget_code_map(db)
    budget_so_set = _build_so_set(db)
    so_service_map = _build_so_service_map(db)
    so_item_counts = _build_so_item_counts(db)
    inv_so_cats = _build_invoice_counts_per_so(invoices)

    # Step 1 + 4: match, then separate OOP from unmatched
    matched_inv, unmatched_inv = _auto_match(db, month, invoices, budget_code_map)
    non_oop_unmatched, oop_inv = _filter_oop(unmatched_inv)

    # Step 2: categorise unmatched
    unmatched_items = _categorise_unmatched(
        non_oop_unmatched, budget_so_set, so_service_map,
        so_item_counts, inv_so_cats,
    )

    # Step 3: new additions
    new_adds = _detect_new_additions(db, unmatched_inv, budget_so_set)

    # Step 5a-pre: reset actuals for this month so re-runs are idempotent
    db.query(BudgetMonthly).filter(BudgetMonthly.month == month).update(
        {BudgetMonthly.actual: 0}, synchronize_session="fetch"
    )
    db.flush()

    # Step 5a: write matched actuals into BudgetMonthly
    _update_actuals(db, month, matched_inv, budget_code_map)

    # Step 6: credit notes
    cn_adjustment = _apply_credit_notes(db, month, budget_code_map)

    # Step 5b: variances (after actuals + credit notes are settled)
    variance_results = calculate_variances(db, month)

    # Step 8: persist recon records
    _persist_reconciliation_records(
        db, month, matched_inv, unmatched_items, budget_code_map,
    )

    # Step 7 / 9: build summary
    total_budget = (
        db.query(func.coalesce(func.sum(BudgetMonthly.expected), 0))
        .filter(BudgetMonthly.month == month)
        .scalar()
    )
    total_invoice = sum(inv.cleaned_item_total or 0 for inv in invoices)
    matched_amount = sum(inv.cleaned_item_total or 0 for inv in matched_inv)
    oop_amount = sum(inv.cleaned_item_total or 0 for inv in oop_inv)

    by_category: dict[str, float] = defaultdict(float)
    for item in unmatched_items:
        by_category[item.category] += item.item_total
    by_category["oop"] = oop_amount

    summary = ReconciliationSummary(
        month=month,
        total_budget_amount=total_budget,
        total_invoice_amount=total_invoice,
        matched_amount=matched_amount,
        unmatched_amount=total_invoice - matched_amount,
        unmatched_by_category=dict(by_category),
        oop_amount=oop_amount,
        credit_note_adjustment=cn_adjustment,
        new_addition_count=len(new_adds),
        matched_count=len(matched_inv),
        unmatched_count=len(unmatched_inv),
    )

    db.commit()
    logger.info(
        "── Reconciliation complete for %s: %d matched, %d unmatched ──",
        month, summary.matched_count, summary.unmatched_count,
    )
    return summary


def run_full_reconciliation(db: Session) -> list[ReconciliationSummary]:
    """Run reconciliation for every month that has invoice data."""
    months_with_data = (
        db.query(Invoice.invoice_month)
        .filter(
            Invoice.invoice_month.isnot(None),
            Invoice.is_voided == False,  # noqa: E712
        )
        .distinct()
        .all()
    )
    month_list = sorted(
        [r[0] for r in months_with_data if r[0]],
        key=lambda m: _month_index(m),
    )

    logger.info("Running full reconciliation for months: %s", month_list)
    summaries: list[ReconciliationSummary] = []
    for m in month_list:
        summaries.append(run_reconciliation(db, m))
    return summaries

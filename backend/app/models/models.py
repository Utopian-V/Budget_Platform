from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, Text,
    ForeignKey, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PARTNER = "partner"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"


class BudgetLevel(str, enum.Enum):
    ORIGINAL = "original"        # Level 1
    NEW_ADDITION = "new_addition"  # Level 2
    DISCREPANCY = "discrepancy"    # Level 3


class ProposalStatus(str, enum.Enum):
    ACCEPTED = "Accepted"
    FOLLOW_UP = "Follow up"
    REJECTED = "Rejected"
    REVISED_ACCEPTED = "Revised and accepted"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    OVERDUE = "Overdue"
    PAID = "Paid"
    PARTIALLY_PAID = "Partially Paid"
    VOID = "Void"
    CLOSED = "Closed"


class SOStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    INVOICED = "invoiced"
    PARTIALLY_INVOICED = "partially_invoiced"
    VOID = "void"
    CLOSED = "closed"


# ─── Master Data ───


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)


class Manager(Base):
    __tablename__ = "managers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)


class Partner(Base):
    __tablename__ = "partners"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)


class BillingEntity(Base):
    __tablename__ = "billing_entities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)


class ServiceCategory(Base):
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)


class VarianceReason(Base):
    __tablename__ = "variance_reasons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reason = Column(String(300), unique=True, nullable=False)


class TrueUpRemark(Base):
    __tablename__ = "true_up_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    remark = Column(String(300), unique=True, nullable=False)


# ─── Budget ───


class BudgetLine(Base):
    __tablename__ = "budget_lines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_no = Column(Integer, nullable=True)
    level = Column(SAEnum(BudgetLevel), default=BudgetLevel.ORIGINAL)

    quotation_no = Column(String(100), nullable=True, index=True)
    sales_order_no = Column(String(100), nullable=True, index=True)
    client_name = Column(String(500), nullable=True, index=True)
    billing_type = Column(String(50), nullable=True)
    billing_entity = Column(String(50), nullable=True)
    partner = Column(String(200), nullable=True)
    manager = Column(String(200), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    service_category = Column(String(300), nullable=True, index=True)
    service_description = Column(Text, nullable=True)

    billing_frequency = Column(String(50), nullable=True)
    no_of_billing = Column(Integer, nullable=True)
    currency = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    budget_base = Column(String(50), nullable=True)
    loe_period_upto = Column(Date, nullable=True)

    existing_fees = Column(Float, nullable=True, default=0)
    pct_increase = Column(Float, nullable=True)
    increased_fees = Column(Float, nullable=True, default=0)
    fee_for_sales_order = Column(Float, nullable=True, default=0)

    # Unique codes (auto-generated)
    unique_code_so = Column(String(300), nullable=True, index=True)
    unique_code_invoice = Column(String(300), nullable=True, index=True)

    # SO value and variance
    sales_order_value = Column(Float, nullable=True, default=0)
    variance = Column(Float, nullable=True, default=0)

    # Amounts carried forward
    amount_carried_forward = Column(Float, nullable=True, default=0)
    check_value = Column(Float, nullable=True)
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    monthly_data = relationship("BudgetMonthly", back_populates="budget_line", cascade="all, delete-orphan")


class BudgetMonthly(Base):
    """One row per budget line per month. Holds expected, actual, variance, and reason."""
    __tablename__ = "budget_monthly"
    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_line_id = Column(Integer, ForeignKey("budget_lines.id"), nullable=False, index=True)
    month = Column(String(10), nullable=False)  # e.g. "Apr-25", "May-25"
    month_index = Column(Integer, nullable=False)  # 0=Apr, 1=May ... 11=Mar

    expected = Column(Float, nullable=True, default=0)
    actual = Column(Float, nullable=True, default=0)
    mtd_variance = Column(Float, nullable=True, default=0)
    ytd_variance = Column(Float, nullable=True, default=0)
    reason = Column(String(300), nullable=True)
    remark = Column(Text, nullable=True)

    budget_line = relationship("BudgetLine", back_populates="monthly_data")

    __table_args__ = (
        UniqueConstraint("budget_line_id", "month", name="uq_budget_monthly"),
    )


# ─── Invoices ───


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)

    invoice_date = Column(Date, nullable=True)
    invoice_number = Column(String(100), nullable=True, index=True)
    invoice_status = Column(String(50), nullable=True)
    customer_name = Column(String(500), nullable=True, index=True)
    billing_entity = Column(String(50), nullable=True)

    place_of_supply = Column(String(100), nullable=True)
    gst_treatment = Column(String(100), nullable=True)
    due_date = Column(Date, nullable=True)
    purchase_order = Column(String(100), nullable=True)
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True, default=1)
    template_name = Column(String(100), nullable=True)

    subtotal = Column(Float, nullable=True, default=0)
    total = Column(Float, nullable=True, default=0)
    balance = Column(Float, nullable=True, default=0)

    # Item-level fields (each row in export is an item)
    item_name = Column(String(300), nullable=True)
    item_desc = Column(Text, nullable=True)
    quantity = Column(Float, nullable=True)
    item_price = Column(Float, nullable=True)
    item_total = Column(Float, nullable=True, default=0)
    account = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    sales_order_number = Column(String(100), nullable=True, index=True)

    # Computed fields
    unique_code = Column(String(300), nullable=True, index=True)
    invoice_month = Column(String(10), nullable=True, index=True)
    is_voided = Column(Boolean, default=False)
    cleaned_item_total = Column(Float, nullable=True, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Sales Orders ───


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)

    order_date = Column(Date, nullable=True)
    salesorder_number = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=True)
    customer_name = Column(String(500), nullable=True, index=True)
    billing_entity = Column(String(50), nullable=True)

    place_of_supply = Column(String(100), nullable=True)
    gst_treatment = Column(String(100), nullable=True)
    gstin = Column(String(50), nullable=True)
    quotation_no = Column(String(100), nullable=True, index=True)
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True, default=1)

    item_name = Column(String(300), nullable=True)
    item_desc = Column(Text, nullable=True)
    quantity_ordered = Column(Float, nullable=True)
    quantity_invoiced = Column(Float, nullable=True)
    quantity_cancelled = Column(Float, nullable=True)
    item_price = Column(Float, nullable=True)
    item_total = Column(Float, nullable=True, default=0)
    account = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    sales_person = Column(String(200), nullable=True)

    unique_code = Column(String(300), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Credit Notes ───


class CreditNote(Base):
    __tablename__ = "credit_notes"
    id = Column(Integer, primary_key=True, autoincrement=True)

    cn_date = Column(Date, nullable=True)
    cn_number = Column(String(100), nullable=True, index=True)
    cn_status = Column(String(50), nullable=True)
    customer_name = Column(String(500), nullable=True, index=True)
    billing_entity = Column(String(50), nullable=True)
    associated_invoice_number = Column(String(100), nullable=True, index=True)

    item_name = Column(String(300), nullable=True)
    item_desc = Column(Text, nullable=True)
    quantity = Column(Float, nullable=True)
    item_total_original = Column(Float, nullable=True, default=0)
    item_total_adjusted = Column(Float, nullable=True, default=0)  # sign-flipped
    account = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # PO looked up from associated invoice
    purchase_order = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Proposals ───


class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, autoincrement=True)

    serial_no = Column(Integer, nullable=True)
    sub_no = Column(String(10), nullable=True)
    year = Column(String(20), nullable=True)
    month = Column(String(20), nullable=True)
    week = Column(String(50), nullable=True)
    period = Column(String(100), nullable=True)
    billing_entity = Column(String(50), nullable=True)
    customer_name = Column(String(500), nullable=True, index=True)
    service_description = Column(Text, nullable=True)
    service_category = Column(String(300), nullable=True)
    department = Column(String(100), nullable=True)
    fee_proposed = Column(Float, nullable=True, default=0)
    status = Column(String(50), nullable=True, index=True)
    follow_up = Column(String(200), nullable=True)
    pic_for_so = Column(String(200), nullable=True)
    quotation_no = Column(String(100), nullable=True, index=True)
    so_number = Column(String(100), nullable=True, index=True)
    remarks = Column(Text, nullable=True)
    additional_remarks = Column(Text, nullable=True)
    quotation_status_zoho = Column(String(50), nullable=True)
    zoho_remarks = Column(Text, nullable=True)
    manager_remark = Column(Text, nullable=True)

    # Aging (computed)
    days_since_proposal = Column(Integer, nullable=True)
    is_stale = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PipelineEntry(Base):
    __tablename__ = "pipeline_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)

    year = Column(String(20), nullable=True)
    week = Column(String(100), nullable=True)
    period = Column(String(100), nullable=True)
    billing_entity = Column(String(50), nullable=True)
    client_name = Column(String(500), nullable=True)
    discussion = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    follow_up = Column(String(200), nullable=True)
    status = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Reconciliation ───


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"
    id = Column(Integer, primary_key=True, autoincrement=True)

    month = Column(String(10), nullable=False, index=True)
    unique_code = Column(String(300), nullable=True, index=True)
    budget_amount = Column(Float, nullable=True, default=0)
    invoice_amount = Column(Float, nullable=True, default=0)
    difference = Column(Float, nullable=True, default=0)

    # Discrepancy categorization
    is_matched = Column(Boolean, default=False)
    discrepancy_type = Column(String(100), nullable=True)
    discrepancy_detail = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Monthly Snapshots ───


class MonthlySnapshot(Base):
    __tablename__ = "monthly_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String(10), nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    data_json = Column(Text, nullable=True)
    created_by = Column(String(200), nullable=True)


# ─── Users ───


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(300), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=True)
    picture = Column(String(500), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.ACCOUNTANT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

"""
Zoho Books API integration.
Pulls invoices, sales orders, credit notes from Zoho Books
and upserts them into the local database.
"""

import logging
from typing import Optional
from datetime import datetime, date

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ZOHO_ACCOUNTS_URL = "https://accounts.zoho.in/oauth/v2/token"
ZOHO_BASE_URL = "https://www.zohoapis.in/books/v3"

MONTH_MAP = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def _invoice_month_label(d: date) -> str:
    """Convert a date to 'Apr-25' style label."""
    return f"{MONTH_MAP[d.month]}-{str(d.year)[2:]}"


class ZohoClient:
    def __init__(self):
        self.client_id = settings.ZOHO_CLIENT_ID
        self.client_secret = settings.ZOHO_CLIENT_SECRET
        self.refresh_token = settings.ZOHO_REFRESH_TOKEN
        self.org_id = settings.ZOHO_ORG_ID
        self.access_token: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.org_id and self.refresh_token)

    async def _ensure_access_token(self):
        if self.access_token:
            return
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                ZOHO_ACCOUNTS_URL,
                data={
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data["access_token"]
            logger.info("Zoho access token refreshed successfully")

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> dict:
        """Exchange a Zoho auth code for access and refresh tokens."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                ZOHO_ACCOUNTS_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            return resp.json()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
        }

    async def _get_all_pages(self, endpoint: str, key: str) -> list:
        """Fetch all pages of a paginated Zoho endpoint."""
        await self._ensure_access_token()
        all_items = []
        page = 1
        while True:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(
                    f"{ZOHO_BASE_URL}/{endpoint}",
                    headers=self._headers(),
                    params={
                        "organization_id": self.org_id,
                        "page": page,
                        "per_page": 200,
                    },
                )
                if resp.status_code == 401:
                    self.access_token = None
                    await self._ensure_access_token()
                    continue
                resp.raise_for_status()
                data = resp.json()

            items = data.get(key, [])
            all_items.extend(items)
            page_context = data.get("page_context", {})
            if not page_context.get("has_more_page", False):
                break
            page += 1

        logger.info(f"Fetched {len(all_items)} {key} from Zoho Books")
        return all_items

    async def get_invoices(self) -> list:
        return await self._get_all_pages("invoices", "invoices")

    async def get_invoice_line_items(self, invoice_id: str) -> list:
        """Fetch line items for a specific invoice."""
        await self._ensure_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{ZOHO_BASE_URL}/invoices/{invoice_id}",
                headers=self._headers(),
                params={"organization_id": self.org_id},
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("invoice", {}).get("line_items", [])

    async def get_sales_orders(self) -> list:
        return await self._get_all_pages("salesorders", "salesorders")

    async def get_salesorder_line_items(self, so_id: str) -> list:
        await self._ensure_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{ZOHO_BASE_URL}/salesorders/{so_id}",
                headers=self._headers(),
                params={"organization_id": self.org_id},
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("salesorder", {}).get("line_items", [])

    async def get_credit_notes(self) -> list:
        return await self._get_all_pages("creditnotes", "creditnotes")

    async def get_creditnote_line_items(self, cn_id: str) -> list:
        await self._ensure_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{ZOHO_BASE_URL}/creditnotes/{cn_id}",
                headers=self._headers(),
                params={"organization_id": self.org_id},
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("creditnote", {}).get("line_items", [])

    def get_status(self) -> dict:
        return {
            "configured": self.is_configured,
            "has_token": self.access_token is not None,
            "org_id": self.org_id if self.is_configured else None,
        }


zoho_client = ZohoClient()


# ── Sync functions that persist Zoho data into the local DB ──

def _parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


async def sync_invoices(db):
    """Pull all invoices from Zoho and upsert into local DB."""
    from app.models.models import Invoice

    raw_invoices = await zoho_client.get_invoices()
    count = 0

    for inv in raw_invoices:
        inv_id = inv.get("invoice_id", "")
        inv_number = inv.get("invoice_number", "")
        inv_date = _parse_date(inv.get("date"))
        customer = inv.get("customer_name", "")
        status = inv.get("status", "")
        total = float(inv.get("total", 0) or 0)
        balance = float(inv.get("balance", 0) or 0)
        currency = inv.get("currency_code", "INR")
        due_date = _parse_date(inv.get("due_date"))
        so_number = inv.get("salesorder_number", "")

        try:
            line_items = await zoho_client.get_invoice_line_items(inv_id)
        except Exception as e:
            logger.warning(f"Failed to fetch line items for invoice {inv_number}: {e}")
            line_items = [{}]

        for item in (line_items or [{}]):
            item_name = item.get("name", "") or item.get("item_name", "")
            item_total = float(item.get("item_total", 0) or 0)
            quantity = float(item.get("quantity", 0) or 0)
            item_price = float(item.get("rate", 0) or 0)
            account = item.get("account_name", "")
            item_desc = item.get("description", "")

            inv_month = _invoice_month_label(inv_date) if inv_date else None
            unique_code = f"{customer}|{item_name}|{so_number}" if customer and item_name else None
            is_voided = status.lower() in ("void", "voided")

            existing = db.query(Invoice).filter(
                Invoice.invoice_number == inv_number,
                Invoice.item_name == item_name,
            ).first()

            if existing:
                existing.invoice_date = inv_date
                existing.invoice_status = status
                existing.customer_name = customer
                existing.total = total
                existing.balance = balance
                existing.currency_code = currency
                existing.due_date = due_date
                existing.item_name = item_name
                existing.item_total = item_total if not is_voided else 0
                existing.cleaned_item_total = item_total if not is_voided else 0
                existing.quantity = quantity
                existing.item_price = item_price
                existing.account = account
                existing.item_desc = item_desc
                existing.sales_order_number = so_number
                existing.unique_code = unique_code
                existing.invoice_month = inv_month
                existing.is_voided = is_voided
            else:
                db.add(Invoice(
                    invoice_date=inv_date,
                    invoice_number=inv_number,
                    invoice_status=status,
                    customer_name=customer,
                    total=total,
                    balance=balance,
                    currency_code=currency,
                    due_date=due_date,
                    item_name=item_name,
                    item_total=item_total if not is_voided else 0,
                    cleaned_item_total=item_total if not is_voided else 0,
                    quantity=quantity,
                    item_price=item_price,
                    account=account,
                    item_desc=item_desc,
                    sales_order_number=so_number,
                    unique_code=unique_code,
                    invoice_month=inv_month,
                    is_voided=is_voided,
                ))
            count += 1

    db.commit()
    logger.info(f"Synced {count} invoice line items from Zoho")
    return count


async def sync_sales_orders(db):
    """Pull all sales orders from Zoho and upsert into local DB."""
    from app.models.models import SalesOrder

    raw_orders = await zoho_client.get_sales_orders()
    count = 0

    for so in raw_orders:
        so_id = so.get("salesorder_id", "")
        so_number = so.get("salesorder_number", "")
        so_date = _parse_date(so.get("date"))
        customer = so.get("customer_name", "")
        status = so.get("status", "")
        currency = so.get("currency_code", "INR")
        quotation_no = so.get("reference_number", "")

        try:
            line_items = await zoho_client.get_salesorder_line_items(so_id)
        except Exception as e:
            logger.warning(f"Failed to fetch line items for SO {so_number}: {e}")
            line_items = [{}]

        for item in (line_items or [{}]):
            item_name = item.get("name", "") or item.get("item_name", "")
            item_total = float(item.get("item_total", 0) or 0)
            quantity_ordered = float(item.get("quantity", 0) or 0)
            quantity_invoiced = float(item.get("quantity_invoiced", 0) or 0)
            item_price = float(item.get("rate", 0) or 0)
            account = item.get("account_name", "")
            item_desc = item.get("description", "")

            unique_code = f"{customer}|{item_name}|{so_number}" if customer and item_name else None

            existing = db.query(SalesOrder).filter(
                SalesOrder.salesorder_number == so_number,
                SalesOrder.item_name == item_name,
            ).first()

            if existing:
                existing.order_date = so_date
                existing.status = status
                existing.customer_name = customer
                existing.currency_code = currency
                existing.quotation_no = quotation_no
                existing.item_name = item_name
                existing.item_total = item_total
                existing.quantity_ordered = quantity_ordered
                existing.quantity_invoiced = quantity_invoiced
                existing.item_price = item_price
                existing.account = account
                existing.item_desc = item_desc
                existing.unique_code = unique_code
            else:
                db.add(SalesOrder(
                    order_date=so_date,
                    salesorder_number=so_number,
                    status=status,
                    customer_name=customer,
                    currency_code=currency,
                    quotation_no=quotation_no,
                    item_name=item_name,
                    item_total=item_total,
                    quantity_ordered=quantity_ordered,
                    quantity_invoiced=quantity_invoiced,
                    item_price=item_price,
                    account=account,
                    item_desc=item_desc,
                    unique_code=unique_code,
                ))
            count += 1

    db.commit()
    logger.info(f"Synced {count} sales order line items from Zoho")
    return count


async def sync_credit_notes(db):
    """Pull all credit notes from Zoho and upsert into local DB."""
    from app.models.models import CreditNote

    raw_notes = await zoho_client.get_credit_notes()
    count = 0

    for cn in raw_notes:
        cn_id = cn.get("creditnote_id", "")
        cn_number = cn.get("creditnote_number", "")
        cn_date = _parse_date(cn.get("date"))
        customer = cn.get("customer_name", "")
        cn_status = cn.get("status", "")
        total = float(cn.get("total", 0) or 0)

        try:
            line_items = await zoho_client.get_creditnote_line_items(cn_id)
        except Exception as e:
            logger.warning(f"Failed to fetch line items for CN {cn_number}: {e}")
            line_items = [{}]

        for item in (line_items or [{}]):
            item_name = item.get("name", "") or item.get("item_name", "")
            item_total = float(item.get("item_total", 0) or 0)
            quantity = float(item.get("quantity", 0) or 0)
            account = item.get("account_name", "")
            item_desc = item.get("description", "")

            existing = db.query(CreditNote).filter(
                CreditNote.cn_number == cn_number,
                CreditNote.item_name == item_name,
            ).first()

            if existing:
                existing.cn_date = cn_date
                existing.cn_status = cn_status
                existing.customer_name = customer
                existing.item_name = item_name
                existing.item_total_original = item_total
                existing.item_total_adjusted = -abs(item_total)
                existing.quantity = quantity
                existing.account = account
                existing.item_desc = item_desc
            else:
                db.add(CreditNote(
                    cn_date=cn_date,
                    cn_number=cn_number,
                    cn_status=cn_status,
                    customer_name=customer,
                    item_name=item_name,
                    item_total_original=item_total,
                    item_total_adjusted=-abs(item_total),
                    quantity=quantity,
                    account=account,
                    item_desc=item_desc,
                ))
            count += 1

    db.commit()
    logger.info(f"Synced {count} credit note line items from Zoho")
    return count

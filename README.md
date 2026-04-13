# Budget Platform

Automated budget reconciliation and reporting platform that replaces manual Excel-based workflows with a web application. Built to integrate with Zoho Books.

## Quick Start

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API calls to the backend on port 8000.

### Import Data

After both servers are running, click the **Import Data** button in the header, or run:

```bash
curl -X POST http://localhost:8000/api/import/all
```

This imports all data from the Excel files in the project directory.

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Backend | Python FastAPI + SQLAlchemy |
| Database | SQLite (local), upgradeable to PostgreSQL |
| Integration | Zoho Books API (stub ready) |

## Features

- **Dashboard** — KPI summary, monthly trend charts, department breakdown
- **Budget Management** — 912 budget lines with monthly expected/actual tracking
- **Invoice Management** — Auto-cleanup of voided invoices and credit note sign correction
- **Reconciliation Engine** — Automated matching of invoices to budget via unique codes, #N/A categorization (direct invoices, previous year SOs, service category mismatches)
- **Variance Analysis** — MTD/YTD variance with reason tracking by department
- **Proposal Lifecycle** — Track proposals from creation through quotation to invoice
- **Reports** — Department variance, MTD/YTD summary, client summary, true-up candidates

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for the interactive API documentation.

## Environment Variables

Create a `.env` file in `backend/` to configure:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_ORG_ID=your_zoho_org_id
```

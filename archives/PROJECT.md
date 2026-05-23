Kasa — Project Brief
What is Kasa?
Kasa is a web app that turns bank statement PDFs into cashflow intelligence for small business owners. Upload your statements, get structured data out, see where your money actually goes, and ask an AI agent questions about your finances in plain language.
Problem
Small business owners in Indonesia typically manage their finances by checking bank balances and scrolling through transaction lists. Their accountant delivers reports monthly or quarterly — too slow for real decision-making. They don't know if they can cover next month's payroll until it's almost due. Reconciling multiple accounts means copy-pasting between PDFs and spreadsheets. Most give up and rely on gut feel.
Who is this for?
SMB owners (1–50 employees) who:

Run their business through 1–3 bank accounts
Receive monthly PDF statements via email
Don't have (or can't afford) a full-time finance person
Make cashflow decisions on gut feel because the data is too painful to extract

Starting segment: Indonesian SMB owners using CIMB Niaga, expanding to BCA, Mandiri, BNI.
Core use cases
1. Statement parsing
Upload a PDF bank statement → get clean, structured transaction data. Automatic categorisation (payroll, supplier payments, revenue, operational costs). Export to CSV/Excel for accountants or personal records.
2. Cashflow dashboard
Income vs. expense trends over time. Top spending categories. Unusual or anomalous transactions flagged. Cash runway projection ("at current burn, you have X months").
3. AI financial chat
Ask questions in natural language (Bahasa or English):

"Berapa total pengeluaran supplier bulan ini vs bulan lalu?"
"Ada transaksi yang nggak biasa minggu ini?"
"Kapan biasanya cash saya paling tipis?"
"Kalau revenue tetap segini, cukup nggak buat 3 bulan ke depan?"

The chat should answer things the dashboard can't surface on its own — custom queries, comparisons, and what-if scenarios.
What Kasa is NOT (for now)

Not an accounting tool (no invoicing, no double-entry bookkeeping)
Not a bank aggregator (no Open Banking API integration — file upload only)
Not a tax preparation tool
Not a replacement for an accountant — it's a complement

MVP scope
Must have

PDF bank statement upload and parsing (CIMB Niaga format first)
Transaction extraction with date, description, amount, balance
Auto-categorisation of transactions
Basic dashboard: income/expense trend, top categories, monthly summary
Export to CSV
AI chat agent that can query the parsed data

Nice to have (post-MVP)

Multi-bank support (BCA, Mandiri, BNI)
Multi-account view with consolidated cashflow
Cash runway projection
Recurring transaction detection
Manual transaction entry
Excel export with formatting
Email-based upload (forward your statement, get analysis back)

Technical direction
<to be discussed>

Frontend: React + Vite
Backend: Bun + Hono (TypeScript)
Database: SQLite
AI: Claude API (for both parsing and chat agent)
File storage: Cloudflare R2-compatible (for uploaded PDFs)

Data model considerations

Support multi-account from day one (even if UI is single-account initially)
Transaction categories should be configurable per user
Keep raw extracted data separate from user-edited/corrected data
Store parsing confidence scores per transaction

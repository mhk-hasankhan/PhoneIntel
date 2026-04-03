# PhoneIntel — Phone Number Validation Tool

A full-stack web app for validating phone numbers via the **Numverify API**.

## Features
- **Single Lookup** — Enter any phone number → get validity, country, carrier, line type
- **Bulk CSV Validation** — Upload a CSV with a phone column → validate all rows
- **Download Results** — Export full results or valid-only as CSV
- Clean dark terminal-style UI

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get a Numverify API Key
Sign up at [https://numverify.com](https://numverify.com) (free tier: 100 requests/month).

### 3. Run the server
```bash
uvicorn main:app --reload
```

Then open: **http://localhost:8000**

---

## Usage

### Single Lookup
1. Paste your Numverify API key in the API Key field at the top
2. Go to the **Single Lookup** tab
3. Enter a phone number (e.g. `+14158586273` or `14158586273`)
4. Optionally enter a 2-letter country code (e.g. `US`, `DE`, `GB`)
5. Click **Lookup**

### Bulk CSV Validation
1. Paste your API key
2. Go to the **Bulk CSV** tab
3. Upload a CSV file — it should have a column named `phone`, `number`, `mobile`, `telephone`, or `tel`
4. Optionally set a default country code
5. Click **Validate CSV**
6. Download results as CSV

### CSV Format Example
```csv
name,phone
Alice,+14155552671
Bob,+4930123456
Charlie,+442071234567
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/validate` | Validate a single number |
| POST | `/api/validate-bulk` | Validate CSV upload |
| POST | `/api/download-csv` | Download results as CSV |

---

## Notes
- The free Numverify tier uses **HTTP** (not HTTPS). Paid plans support HTTPS.
- Rate limits depend on your Numverify plan.
- The backend proxies requests to Numverify to keep your API key server-side.

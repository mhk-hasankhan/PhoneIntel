from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import httpx
import csv
import io
import os
import json
from typing import Optional

app = FastAPI(title="Phone Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

NUMVERIFY_BASE = "http://apilayer.net/api/validate"

def build_numverify_url(phone: str, country_code: str = "", api_key: str = "") -> str:
    params = f"?access_key={api_key}&number={phone}&country_code={country_code}&format=1"
    return NUMVERIFY_BASE + params


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/validate")
async def validate_single(phone: str, country_code: str = "", api_key: str = ""):
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")

    url = build_numverify_url(phone, country_code, api_key)

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            data = resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Numverify request failed: {str(e)}")

    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"].get("info", "Numverify error"))

    return {
        "number": data.get("number", phone),
        "valid": data.get("valid", False),
        "local_format": data.get("local_format", ""),
        "international_format": data.get("international_format", ""),
        "country_prefix": data.get("country_prefix", ""),
        "country_code": data.get("country_code", ""),
        "country_name": data.get("country_name", ""),
        "location": data.get("location", ""),
        "carrier": data.get("carrier", ""),
        "line_type": data.get("line_type", ""),
    }


@app.post("/api/validate-bulk")
async def validate_bulk(file: UploadFile = File(...), api_key: str = "", country_code: str = ""):
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        # Try treating as single-column no-header CSV
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        rows = [{"phone": l} for l in lines]

    # Detect phone column
    phone_col = None
    if rows:
        for candidate in ["phone", "phone_number", "number", "mobile", "tel", "telephone", "Phone", "Number"]:
            if candidate in rows[0]:
                phone_col = candidate
                break
        if not phone_col:
            phone_col = list(rows[0].keys())[0]

    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        for row in rows:
            phone = str(row.get(phone_col, "")).strip()
            if not phone:
                continue
            url = build_numverify_url(phone, country_code, api_key)
            try:
                resp = await client.get(url)
                data = resp.json()
                if "error" in data:
                    result = {**row, "valid": False, "country_name": "", "carrier": "", "line_type": "", "international_format": "", "error": data["error"].get("info", "Error")}
                else:
                    result = {
                        **row,
                        "valid": data.get("valid", False),
                        "international_format": data.get("international_format", ""),
                        "country_name": data.get("country_name", ""),
                        "location": data.get("location", ""),
                        "carrier": data.get("carrier", ""),
                        "line_type": data.get("line_type", ""),
                        "error": ""
                    }
            except Exception as e:
                result = {**row, "valid": False, "country_name": "", "carrier": "", "line_type": "", "international_format": "", "error": str(e)}
            results.append(result)

    return {"results": results, "total": len(results), "valid": sum(1 for r in results if r.get("valid"))}


@app.post("/api/download-csv")
async def download_csv(payload: dict):
    results = payload.get("results", [])
    if not results:
        raise HTTPException(status_code=400, detail="No results to download")

    output = io.StringIO()
    fieldnames = list(results[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=validated_numbers.csv"}
    )

# Sahi Scan Backend

FastAPI backend for the Sahi Scan React/Vite frontend.

## Run locally

```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs
Health: http://localhost:8000/health

### Demo account
- Email: `demo@sahiscan.local`
- Password: `SahiScan123!`

The backend seeds two demo products and three profiles on first start. Replace the demo credentials and `SAHI_SECRET_KEY` before deployment.

## Core endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/profiles`
- `POST /api/v1/profiles`
- `POST /api/v1/scans`
- `POST /api/v1/scans/image`
- `GET /api/v1/scans`
- `GET /api/v1/scans/{id}`
- `DELETE /api/v1/scans/{id}`
- `GET /api/v1/favorites`
- `POST /api/v1/favorites/{scan_id}`
- `DELETE /api/v1/favorites/{scan_id}`
- `POST /api/v1/chat`

## Complete image / OCR workflow

`POST /api/v1/scans/image` now performs the full backend pipeline:

1. validates and stores the uploaded JPG/PNG/WebP image
2. preprocesses the image for OCR
3. reads QR/2D codes and attempts OpenCV barcode decoding
4. falls back to OCR-extracted printed barcode digits for EAN/UPC-style codes
5. extracts product name, FSSAI licence digits, ingredients and nutrition fields when present
6. matches the detected barcode against the local product evidence database
7. if no known product matches, creates an **OCR-only / partial evidence** product record instead of inventing verified product data
8. runs the deterministic profile evaluation
9. stores the image path, OCR evidence and scan result in the database
10. returns the complete scan response to the Android/Capacitor frontend

### OCR runtime dependency

Python package `pytesseract` is included in `requirements.txt`. Tesseract OCR itself is a separate native executable and must be installed on the machine running FastAPI. If it is not on PATH, set `pytesseract.pytesseract.tesseract_cmd` in `app/services/ocr.py` or add the executable directory to PATH.

OCR results are evidence extraction. The app intentionally returns `UNCLEAR`/partial evidence when required fields cannot be established; it does not manufacture missing nutrition or regulatory facts.

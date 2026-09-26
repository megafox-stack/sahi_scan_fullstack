from __future__ import annotations
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

NUTRIENT_PATTERNS = {
    "sodium": [r"sodium\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*mg", r"salt\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
    "sugar": [r"(?:total\s+)?sugars?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
    "carbs": [r"(?:total\s+)?carbohydrate[s]?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
    "fat": [r"(?<!saturated\s)(?:total\s+)?fat\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
    "sat_fat": [r"saturated\s+fat\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
    "energy": [r"energy\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*kcal"],
    "protein": [r"protein\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
    "fiber": [r"(?:dietary\s+)?f(?:i|1)ber\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g"],
}

def _clean(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def _decode_codes(img: np.ndarray) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if img is None or not hasattr(cv2, "barcode"):
        return found

    height, width = img.shape[:2]
    scale = min(1.0, 2000 / max(height, width))
    working = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else img
    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY) if len(working.shape) == 3 else working
    variants = [working, gray, cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE), cv2.rotate(gray, cv2.ROTATE_180), cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)]
    detector = cv2.barcode.BarcodeDetector()
    qr = cv2.QRCodeDetector()
    seen = set()
    for variant in variants:
        try:
            value, _, _ = qr.detectAndDecode(variant)
            if value and ("QR", value) not in seen:
                found.append({"type": "QR", "value": value})
                seen.add(("QR", value))
        except Exception:
            pass
        try:
            ok, decoded, types, _ = detector.detectAndDecode(variant)
            type_values = list(types) if types is not None else []
            if ok and decoded is not None:
                for value, code_type in zip(list(decoded), type_values):
                    value = str(value)
                    code_type = str(code_type)
                    if value and (code_type, value) not in seen:
                        found.append({"type": code_type, "value": value})
                        seen.add((code_type, value))
        except Exception:
            pass
    return found

def _ocr_text(img: Image.Image) -> tuple[str, str | None]:
    if pytesseract is None:
        return "", "pytesseract is not installed"
    variants = []
    base = ImageOps.exif_transpose(img).convert("RGB")
    gray = np.array(ImageOps.grayscale(base))
    up = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    variants.append(up)
    variants.append(cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
    texts = []
    for variant in variants:
        try:
            texts.append(pytesseract.image_to_string(variant, config="--psm 6"))
        except Exception as exc:
            return "", f"Tesseract OCR failed: {exc}"
    text = max(texts, key=len, default="")
    return _clean(text), None

def _extract_fields(text: str, codes: list[dict[str, str]]) -> dict[str, Any]:
    low = text.lower()
    barcodes = [x["value"] for x in codes if re.fullmatch(r"\d{8,14}", x["value"])]
    # preserve order and remove duplicates
    barcodes = list(dict.fromkeys(barcodes))
    # FSSAI licence digits are not a product barcode. Keep them in their own field.
    m_license = re.search(r"(?:fssai|lic(?:ence|ense)?)[^0-9]{0,20}(\d{10,14})", text, re.I)
    if m_license:
        barcodes = [x for x in barcodes if x != m_license.group(1)]
    nutrition: dict[str, float | None] = {k: None for k in NUTRIENT_PATTERNS}
    for key, patterns in NUTRIENT_PATTERNS.items():
        for pattern in patterns:
            m = re.search(pattern, low, flags=re.I)
            if m:
                value = float(m.group(1))
                # salt is often reported in grams; convert it to sodium approximately only
                # when no explicit sodium field exists.
                if key == "sodium" and "salt" in m.group(0).lower() and "sodium" not in m.group(0).lower():
                    value = value * 393.4
                nutrition[key] = value
                break
    ingredients = []
    m = re.search(r"ingredients?\s*[:\-]?\s*(.+?)(?:\n\s*(?:nutrition|nutritional|allergen|contains|manufactured|fssai|net\s*quantity)\b|$)", text, re.I | re.S)
    if m:
        raw = re.sub(r"\s+", " ", m.group(1)).strip(" .;:")
        ingredients = [x.strip(" .") for x in re.split(r",|;", raw) if 2 <= len(x.strip()) <= 160]
    name = None
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in lines[:8]:
        if not re.search(r"ingredients?|nutrition|energy|sodium|sugar|fssai|barcode|batch|net quantity", line, re.I) and 3 <= len(line) <= 120:
            name = line
            break
    fssai_license = None
    m = re.search(r"(?:fssai|lic(?:ence|ense)?)[^0-9]{0,20}(\d{10,14})", text, re.I)
    if m:
        fssai_license = m.group(1)
    return {"barcodes": barcodes, "nutrition": nutrition, "ingredients": ingredients, "name": name, "fssai_license": fssai_license}

def analyze_image(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    try:
        image = Image.open(path)
        image.verify()
        image = Image.open(path)
    except Exception as exc:
        return {"status": "UNCLEAR", "error": f"Invalid image: {exc}", "text": "", "codes": [], "fields": {}}
    cv_image = None
    try:
        oriented = ImageOps.exif_transpose(image).convert("RGB")
        cv_image = cv2.cvtColor(np.array(oriented), cv2.COLOR_RGB2BGR)
    except Exception:
        cv_image = cv2.imread(str(path))
    codes = _decode_codes(cv_image) if cv_image is not None else []
    text, error = _ocr_text(image)
    fields = _extract_fields(text, codes)
    status = "AGREED" if fields["barcodes"] or fields["nutrition"]["sodium"] is not None or fields["nutrition"]["sugar"] is not None or fields["ingredients"] else "UNCLEAR"
    return {"status": status, "text": text, "codes": codes, "fields": fields, "ocr_error": error, "image": {"width": image.width, "height": image.height}}

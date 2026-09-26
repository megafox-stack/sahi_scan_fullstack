from pathlib import Path

def ingredient_to_dict(i):
    return {"name": i.name, "normalized_name": i.normalized_name, "function": i.function, "additive_code": i.additive_code, "type": i.type, "note": i.note, "image": i.image}

def product_to_dict(p):
    n = p.nutrition
    return {"id": p.id, "barcode": p.barcode, "code_type": p.code_type, "name": p.name, "brand": p.brand, "category": p.category, "manufacturer": p.manufacturer, "marketer": p.marketer, "fssai": p.fssai, "fssai_license": p.fssai_license, "fssai_status": p.fssai_status, "fssai_source_url": p.fssai_source_url, "evidence_status": p.evidence_status, "source": p.source, "source_url": p.source_url, "image": p.image, "image_url": p.image_url, "nutrition": ({"sodium": n.sodium, "sugar": n.sugar, "carbs": n.carbs, "fat": n.fat, "sat_fat": n.sat_fat, "energy": n.energy, "trans_fat": n.trans_fat, "added_sugar": n.added_sugar, "protein": n.protein, "fiber": n.fiber, "serving_size": n.serving_size, "serving_unit": n.serving_unit, "source": n.source} if n else {}), "ingredients": [ingredient_to_dict(i) for i in p.ingredients], "alternatives": [], "reports": {"total": len(getattr(p, "quality_reports", []) or []), "spoilage": 0, "foreignObject": 0}, "allergens": [{"name": a.name, "source": a.source} for a in p.allergens]}

def _captured_image_url(path):
    if not path:
        return None
    upload_root = Path(__file__).resolve().parents[2] / "uploads"
    candidate = Path(path)
    try:
        relative = candidate.resolve().relative_to(upload_root.resolve()) if candidate.is_absolute() else candidate
    except (OSError, ValueError):
        return None
    normalized = relative.as_posix().lstrip("/")
    if not normalized or ".." in Path(normalized).parts:
        return None
    if normalized.startswith("uploads/"):
        normalized = normalized[len("uploads/"):]
    return f"/uploads/{normalized}"

def scan_to_dict(s):
    captured_path = s.captured_image_path or s.image_path
    analysis = s.analysis or {}
    ocr = analysis.get("ocr") or {}
    return {"id": s.id, "created_at": s.created_at, "sahi_score": s.sahi_score, "status": s.status, "verdict": s.verdict, "reason": analysis.get("reason", ""), "analysis": analysis, "image_path": s.image_path, "captured_image_path": captured_path, "captured_image_url": _captured_image_url(captured_path), "ocr_text": s.ocr_text or ocr.get("text"), "barcode": s.barcode or analysis.get("barcode"), "product": product_to_dict(s.product) if s.product else None, "profile_id": s.profile_id}

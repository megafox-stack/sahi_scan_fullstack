def ingredient_to_dict(i):
    return {"name": i.name, "normalized_name": i.normalized_name, "function": i.function, "additive_code": i.additive_code, "type": i.type, "note": i.note, "image": i.image}

def product_to_dict(p):
    n = p.nutrition
    return {"id": p.id, "barcode": p.barcode, "code_type": p.code_type, "name": p.name, "brand": p.brand, "category": p.category, "manufacturer": p.manufacturer, "marketer": p.marketer, "fssai": p.fssai, "fssai_license": p.fssai_license, "fssai_status": p.fssai_status, "fssai_source_url": p.fssai_source_url, "evidence_status": p.evidence_status, "source": p.source, "source_url": p.source_url, "image": p.image, "nutrition": ({"sodium": n.sodium, "sugar": n.sugar, "carbs": n.carbs, "fat": n.fat, "sat_fat": n.sat_fat, "energy": n.energy, "trans_fat": n.trans_fat, "added_sugar": n.added_sugar, "protein": n.protein, "fiber": n.fiber, "serving_size": n.serving_size, "serving_unit": n.serving_unit, "source": n.source} if n else {}), "ingredients": [ingredient_to_dict(i) for i in p.ingredients], "alternatives": [], "reports": {"total": len(getattr(p, "quality_reports", []) or []), "spoilage": 0, "foreignObject": 0}, "allergens": [{"name": a.name, "source": a.source} for a in p.allergens]}

def scan_to_dict(s):
    return {"id": s.id, "created_at": s.created_at, "sahi_score": s.sahi_score, "status": s.status, "verdict": s.verdict, "reason": s.analysis.get("reason", ""), "analysis": s.analysis, "image_path": s.image_path, "product": product_to_dict(s.product) if s.product else None, "profile_id": s.profile_id}

def evaluate(product, profile):
    reasons = []
    n = product.nutrition
    if n is None:
        return {"score": None, "status": "UNCLEAR", "verdict": "UNCLEAR", "reason": "No nutrition evidence is available.", "reasons": ["No nutrition evidence is available."], "evidence_status": "UNCLEAR"}
    if n.sodium is not None and profile.sodium_mg is not None and n.sodium > profile.sodium_mg:
        reasons.append(f"Sodium is {n.sodium:g} mg/100 g, above {profile.sodium_mg:g} mg/100 g for {profile.name}.")
    if n.sugar is not None and profile.sugar_g is not None and n.sugar > profile.sugar_g:
        reasons.append(f"Sugar is {n.sugar:g} g/100 g, above {profile.sugar_g:g} g/100 g for {profile.name}.")
    required_missing = []
    if profile.sodium_mg is not None and n.sodium is None: required_missing.append("sodium")
    if profile.sugar_g is not None and n.sugar is None: required_missing.append("sugar")
    if reasons:
        return {"score": None, "status": "DISAGREED", "verdict": "DISAGREED", "reason": " ".join(reasons), "reasons": reasons, "evidence_status": product.evidence_status or "PARTIAL"}
    if required_missing:
        reason = "Required nutrition evidence is missing: " + ", ".join(required_missing) + "."
        return {"score": None, "status": "UNCLEAR", "verdict": "UNCLEAR", "reason": reason, "reasons": [reason], "evidence_status": "PARTIAL"}
    return {"score": 100.0, "status": "AGREED", "verdict": "AGREED", "reason": f"Available declared nutrition evidence matches {profile.name}'s configured preferences.", "reasons": [], "evidence_status": product.evidence_status or "VERIFIED"}

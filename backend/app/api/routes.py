from pathlib import Path
from uuid import uuid4
from datetime import datetime
from io import BytesIO
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.api.deps import current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User, Profile, Product, Scan, Favorite, Nutrition, Ingredient
from app.schemas.schemas import AuthRegister, AuthLogin, Token, ProfileCreate, ProfileOut, ScanRequest, ChatRequest, QualityReportCreate, QualityReportOut
from app.services.scoring import evaluate
from app.services.serializers import product_to_dict, scan_to_dict
from app.services.ocr import analyze_image, _extract_fields

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/auth/guest", response_model=Token)
def guest_login(db: Session = Depends(get_db)):
    """Temporary device-testing account; remove or disable before deployment."""
    email = "device-guest@sahiscan.local"
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email, password_hash=hash_password(uuid4().hex), name="Device Guest")
        db.add(user); db.flush()
        db.add(Profile(user_id=user.id, name="Me", profile_type="Custom", icon="🙂", sodium_mg=600, sugar_g=10))
        db.commit(); db.refresh(user)
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}

@router.post("/auth/register", response_model=Token)
def register(data: AuthRegister, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first(): raise HTTPException(409, "Email already registered")
    user = User(email=data.email.lower(), password_hash=hash_password(data.password), name=data.name); db.add(user); db.flush()
    db.add(Profile(user_id=user.id, name="Me", profile_type="Custom", icon="🙂", sodium_mg=600, sugar_g=10)); db.commit()
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}

@router.post("/auth/login", response_model=Token)
def login(data: AuthLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}

@router.get("/profiles", response_model=list[ProfileOut])
def profiles(user=Depends(current_user), db: Session = Depends(get_db)): return db.query(Profile).filter_by(user_id=user.id).all()

@router.post("/profiles", response_model=ProfileOut)
def create_profile(data: ProfileCreate, user=Depends(current_user), db: Session = Depends(get_db)):
    p = Profile(user_id=user.id, **data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

@router.patch("/profiles/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: int, data: ProfileCreate, user=Depends(current_user), db: Session = Depends(get_db)):
    p = db.query(Profile).filter_by(id=profile_id, user_id=user.id).first()
    if not p: raise HTTPException(404, "Profile not found")
    for k,v in data.model_dump().items(): setattr(p,k,v)
    db.commit(); db.refresh(p); return p

def _profile(data_profile_id, user, db):
    p = db.query(Profile).filter_by(id=data_profile_id, user_id=user.id).first() if data_profile_id else db.query(Profile).filter_by(user_id=user.id).first()
    if not p: raise HTTPException(400, "Create a profile before scanning")
    return p

def _save_scan(db, user, profile, product, analysis, image_path=None, ocr_text=None, barcode=None):
    result = evaluate(product, profile) if product else {
        "score": None,
        "status": "UNCLEAR",
        "verdict": "UNCLEAR",
        "reason": "Product details were not identified from this scan.",
        "reasons": ["Product details were not identified from this scan."],
        "evidence_status": "UNCLEAR",
    }
    merged = {**analysis, **result}
    s = Scan(user_id=user.id, profile_id=profile.id, product_id=product.id if product else None, captured_image_path=image_path, image_path=image_path, ocr_text=ocr_text, barcode=barcode, sahi_score=result["score"], status=result["status"], verdict=result["verdict"], analysis=merged)
    db.add(s); db.commit(); db.refresh(s); return s

@router.post("/scans", response_model=dict)
def scan(data: ScanRequest, user=Depends(current_user), db: Session = Depends(get_db)):
    product = db.query(Product).options(joinedload(Product.nutrition), joinedload(Product.ingredients)).filter_by(barcode=data.barcode).first()
    if not product: raise HTTPException(404, "Product barcode not found")
    return scan_to_dict(_save_scan(db, user, _profile(data.profile_id, user, db), product, {"source": "barcode", "barcode": data.barcode}, barcode=data.barcode))

@router.post("/scans/image", response_model=dict)
async def scan_image(file: UploadFile = File(...), profile_id: int | None = Form(None), barcode: str | None = Form(None), ocr_text: str | None = Form(None), user=Depends(current_user), db: Session = Depends(get_db)):
    content_types = {"JPEG": ("image/jpeg", ".jpg"), "PNG": ("image/png", ".png"), "WEBP": ("image/webp", ".webp")}
    data = await file.read()
    if len(data) > 10 * 1024 * 1024: raise HTTPException(413, "Image must be under 10 MB")
    if not data: raise HTTPException(415, "The uploaded file is empty")
    try:
        image = Image.open(BytesIO(data))
        image_format = image.format
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(415, "The uploaded file is not a valid JPG, PNG or WebP image")
    if image_format not in content_types:
        raise HTTPException(415, "Use a valid JPG, PNG or WebP image")
    expected_type, suffix = content_types[image_format]
    if file.content_type and file.content_type not in {expected_type, "application/octet-stream"}:
        raise HTTPException(415, "The uploaded image format does not match its content type")
    if barcode and len(barcode.strip()) > 32:
        raise HTTPException(422, "Barcode must be 32 characters or fewer")

    profile = _profile(profile_id, user, db)
    scan_dir = UPLOAD_DIR / "scans"
    scan_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    target = scan_dir / filename
    target.write_bytes(data)

    image_ocr = analyze_image(target)
    extracted_text = (ocr_text or "").strip() or image_ocr.get("text", "")
    fields = _extract_fields(extracted_text, image_ocr.get("codes", []))
    detected_barcode = (barcode or "").strip() or (fields.get("barcodes") or [None])[0]
    if detected_barcode and detected_barcode not in fields.get("barcodes", []):
        fields.setdefault("barcodes", []).insert(0, detected_barcode)
    ocr = {**image_ocr, "text": extracted_text, "fields": fields, "source": "android_tesseract" if ocr_text and ocr_text.strip() else "backend_tesseract"}
    if ocr_text and ocr_text.strip():
        ocr["ocr_error"] = None

    product_query = db.query(Product).options(joinedload(Product.nutrition), joinedload(Product.ingredients), joinedload(Product.allergens))
    product = product_query.filter_by(barcode=detected_barcode).first() if detected_barcode else None
    if not product and not detected_barcode and fields.get("name"):
        product = product_query.filter(
            Product.barcode.is_(None),
            Product.source == "OCR label",
            func.lower(Product.name) == fields["name"].strip().lower(),
        ).first()
    created_from_ocr = False
    if not product and fields.get("name"):
        # OCR can identify a real label even when no barcode was captured.
        # Store only extracted facts; a nullable barcode allows that Product
        # to be linked to this Scan without manufacturing an identifier.
        product = Product(barcode=detected_barcode, code_type="OCR", name=fields["name"], brand="", category="", manufacturer="", fssai="Not verified", fssai_license=fields.get("fssai_license"), fssai_status="OCR_ONLY" if fields.get("fssai_license") else "NOT_LOADED", evidence_status="PARTIAL", source="OCR label", source_url=None, image="", image_url=None)
        db.add(product); db.flush()
        n = fields.get("nutrition", {})
        if any(v is not None for v in n.values()):
            db.add(Nutrition(product_id=product.id, sodium=n.get("sodium"), sugar=n.get("sugar"), carbs=n.get("carbs"), fat=n.get("fat"), sat_fat=n.get("sat_fat"), energy=n.get("energy"), protein=n.get("protein"), fiber=n.get("fiber"), source="OCR label"))
        for raw in fields.get("ingredients", []):
            normalized = raw.lower().strip()
            additive = None
            import re
            m = re.search(r"\bINS\s*[- ]?(\d{3,4})\b", raw, re.I)
            if m: additive = "INS " + m.group(1)
            db.add(Ingredient(product_id=product.id, name=raw, normalized_name=normalized, additive_code=additive, type="blue" if additive else "green", note="Extracted from uploaded label by OCR."))
        db.commit(); db.refresh(product); created_from_ocr = True
    analysis = {"source": "image_ocr", "ocr": ocr, "barcode": detected_barcode, "product_match": bool(product and not created_from_ocr)}
    result = _save_scan(db, user, profile, product, analysis, f"scans/{filename}", extracted_text or None, detected_barcode)
    return scan_to_dict(result) | {"workflow": {"image_stored": True, "ocr_completed": bool(extracted_text), "barcode_detected": bool(detected_barcode), "product_matched": bool(product and not created_from_ocr), "product_created_from_ocr": created_from_ocr, "next_step": "Review extracted fields before relying on OCR-only evidence."}}

@router.get("/scans", response_model=list[dict])
def recent_scans(limit: int = 20, user=Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Scan).options(joinedload(Scan.product).joinedload(Product.nutrition), joinedload(Scan.product).joinedload(Product.ingredients), joinedload(Scan.product).joinedload(Product.allergens)).filter_by(user_id=user.id).order_by(Scan.created_at.desc()).limit(min(limit,100)).all(); return [scan_to_dict(s) for s in rows]

@router.delete("/scans")
def clear_recent_scans(user=Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Scan).filter_by(user_id=user.id).all()
    image_paths = [s.captured_image_path or s.image_path for s in rows]
    scan_ids = [s.id for s in rows]
    if scan_ids:
        db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.scan_id.in_(scan_ids)).delete(synchronize_session=False)
        db.query(Scan).filter(Scan.user_id == user.id, Scan.id.in_(scan_ids)).delete(synchronize_session=False)
        db.commit()
    for relative_path in image_paths:
        if not relative_path:
            continue
        image_path = (UPLOAD_DIR / relative_path).resolve()
        try:
            image_path.relative_to(UPLOAD_DIR.resolve())
        except ValueError:
            continue
        if image_path.is_file():
            image_path.unlink()
    return {"deleted": len(scan_ids)}

@router.get("/scans/{scan_id}", response_model=dict)
def get_scan(scan_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    s = db.query(Scan).options(joinedload(Scan.product).joinedload(Product.nutrition), joinedload(Scan.product).joinedload(Product.ingredients), joinedload(Scan.product).joinedload(Product.allergens)).filter_by(id=scan_id,user_id=user.id).first()
    if not s: raise HTTPException(404,"Scan not found")
    return scan_to_dict(s)

@router.delete("/scans/{scan_id}")
def delete_scan(scan_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    s=db.query(Scan).filter_by(id=scan_id,user_id=user.id).first()
    if not s: raise HTTPException(404,"Scan not found")
    db.delete(s); db.commit(); return {"deleted":True}

@router.get("/products/{barcode}")
def product_by_barcode(barcode: str, user=Depends(current_user), db: Session=Depends(get_db)):
    p=db.query(Product).options(joinedload(Product.nutrition), joinedload(Product.ingredients)).filter_by(barcode=barcode).first()
    if not p: raise HTTPException(404,"Product not found")
    return product_to_dict(p)

@router.get("/favorites", response_model=list[dict])
def favorites(user=Depends(current_user), db: Session=Depends(get_db)):
    out=[]
    for f in db.query(Favorite).filter_by(user_id=user.id).all():
        s=db.query(Scan).options(joinedload(Scan.product).joinedload(Product.nutrition), joinedload(Scan.product).joinedload(Product.ingredients)).filter_by(id=f.scan_id).first()
        if s: out.append(scan_to_dict(s))
    return out

@router.post("/favorites/{scan_id}")
def add_favorite(scan_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    if not db.query(Scan).filter_by(id=scan_id,user_id=user.id).first(): raise HTTPException(404,"Scan not found")
    if not db.query(Favorite).filter_by(user_id=user.id,scan_id=scan_id).first(): db.add(Favorite(user_id=user.id,scan_id=scan_id)); db.commit()
    return {"saved":True}

@router.delete("/favorites/{scan_id}")
def remove_favorite(scan_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    f=db.query(Favorite).filter_by(user_id=user.id,scan_id=scan_id).first()
    if f: db.delete(f); db.commit()
    return {"saved":False}

@router.post("/reports", response_model=QualityReportOut)
def create_report(data: QualityReportCreate, user=Depends(current_user), db:Session=Depends(get_db)):
    from app.models import QualityReport
    r=QualityReport(user_id=user.id, **data.model_dump()); db.add(r); db.commit(); db.refresh(r); return r

@router.get("/complaints/options")
def complaint_options(user=Depends(current_user)):
    return {"live_submission":False,"official_portal":"https://foscos.fssai.gov.in/consumergrievance","message":"Use the official FSSAI Food Safety Connect / complaint pathway. Sahi Scan does not claim to submit a complaint directly."}

@router.get("/dart")
def dart(food: str|None=None, user=Depends(current_user), db:Session=Depends(get_db)):
    from app.models import DartCheck
    q=db.query(DartCheck)
    if food: q=q.filter(DartCheck.food.ilike(food))
    return [{"id":x.id,"food":x.food,"adulterant":x.adulterant,"title":x.title,"steps":x.steps,"expected_observation":x.expected_observation,"caution":x.caution,"source":x.source,"source_url":x.source_url} for x in q.all()]

@router.get("/dart/{check_id}")
def dart_one(check_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    from app.models import DartCheck
    x=db.query(DartCheck).filter_by(id=check_id).first()
    if not x: raise HTTPException(404,"DART check not found")
    return {"id":x.id,"food":x.food,"adulterant":x.adulterant,"title":x.title,"steps":x.steps,"expected_observation":x.expected_observation,"caution":x.caution,"source":x.source,"source_url":x.source_url}

@router.post("/chat")
def chat(data:ChatRequest,user=Depends(current_user),db:Session=Depends(get_db)):
    msg=data.message.lower()
    if "sugar" in msg: reply="Check sugar per 100 g and compare it with the active profile preference."
    elif "sodium" in msg or "salt" in msg: reply="Check sodium per 100 g; Sahi Scan uses the active profile threshold when evaluating a scan."
    elif "ocr" in msg or "image" in msg: reply="An uploaded label is preprocessed, OCR-read, checked for QR/barcode data, parsed for nutrition and ingredients, then matched to a known product when possible."
    elif "ingredient" in msg: reply="Open Ingredient Intelligence in the scan result to inspect extracted or declared ingredients."
    else: reply="I can explain the product, OCR evidence, ingredients, nutrition and profile match from the information available in Sahi Scan."
    return {"reply":reply,"language":data.language}

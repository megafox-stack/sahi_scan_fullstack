from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine
from app.models import models
from app.db.migrate import ensure_schema
from app.api.routes import router
from app.seed import seed_database

ensure_schema()
Base.metadata.create_all(bind=engine)
seed_database()

app = FastAPI(title="Sahi Scan API", version="1.2.0", description="Evidence-first food analysis backend with image/OCR processing.")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
allow_creds = False if "*" in origins else True
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_origin_regex=r"https?://192\.168\.0\.\d+(?::\d+)?", allow_credentials=allow_creds, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sahi-scan-api", "image_workflow": True}

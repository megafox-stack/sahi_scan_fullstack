from sqlalchemy import inspect, text
from app.db.session import Base, engine
from app.models import models  # noqa: F401

def ensure_schema():
    Base.metadata.create_all(bind=engine)
    # SQLite-safe additive migration for databases created by the earlier MVP.
    additions = {
        "products": {
            "code_type":"VARCHAR(40)","marketer":"VARCHAR(180)","fssai_license":"VARCHAR(32)","fssai_status":"VARCHAR(40)","fssai_source_url":"VARCHAR(500)","fssai_verified_at":"DATETIME","evidence_status":"VARCHAR(30)","source":"VARCHAR(120)","source_url":"VARCHAR(500)"
        },
        "nutrition": {"trans_fat":"FLOAT","added_sugar":"FLOAT","protein":"FLOAT","fiber":"FLOAT","serving_size":"FLOAT","serving_unit":"VARCHAR(20)","source":"VARCHAR(120)"},
        "ingredients": {"normalized_name":"VARCHAR(160)","function":"VARCHAR(120)","additive_code":"VARCHAR(30)"},
    }
    with engine.begin() as conn:
        inspector = inspect(engine)
        for table, cols in additions.items():
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, sql_type in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))

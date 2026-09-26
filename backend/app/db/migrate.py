from sqlalchemy import inspect, text
from app.db.session import Base, engine
from app.models import models  # noqa: F401

def ensure_schema():
    Base.metadata.create_all(bind=engine)
    # SQLite-safe additive migration for databases created by the earlier MVP.
    additions = {
        "products": {
            "code_type":"VARCHAR(40)","marketer":"VARCHAR(180)","fssai_license":"VARCHAR(32)","fssai_status":"VARCHAR(40)","fssai_source_url":"VARCHAR(500)","fssai_verified_at":"DATETIME","evidence_status":"VARCHAR(30)","source":"VARCHAR(120)","source_url":"VARCHAR(500)","image_url":"VARCHAR(500)","ingredients_text":"TEXT","nutrition_grade":"VARCHAR(8)"
        },
        "scans": {"captured_image_path":"VARCHAR(500)","ocr_text":"TEXT","barcode":"VARCHAR(32)"},
        "nutrition": {"trans_fat":"FLOAT","added_sugar":"FLOAT","protein":"FLOAT","fiber":"FLOAT","serving_size":"FLOAT","serving_unit":"VARCHAR(20)","source":"VARCHAR(120)"},
        "ingredients": {"normalized_name":"VARCHAR(160)","function":"VARCHAR(120)","additive_code":"VARCHAR(30)"},
    }
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            # These pragmas must be set before beginning the table migration.
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(text("PRAGMA legacy_alter_table=ON"))
            conn.commit()
        transaction = conn.begin()
        inspector = inspect(engine)
        for table, cols in additions.items():
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, sql_type in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
        # SQLite cannot alter a column's nullability in place. Rebuild only
        # the legacy products table whose barcode was originally NOT NULL.
        if engine.dialect.name == "sqlite":
            barcode_column = next((c for c in inspector.get_columns("products") if c["name"] == "barcode"), None)
            if barcode_column and barcode_column.get("nullable") is False:
                conn.execute(text("PRAGMA foreign_keys=OFF"))
                conn.execute(text("ALTER TABLE products RENAME TO products_barcode_migration"))
                conn.execute(text("DROP INDEX IF EXISTS ix_products_barcode"))
                Base.metadata.tables["products"].create(bind=conn)
                old_columns = {c["name"] for c in inspector.get_columns("products")}
                new_columns = [c.name for c in Base.metadata.tables["products"].columns if c.name in old_columns]
                names = ", ".join(f'"{name}"' for name in new_columns)
                conn.execute(text(f'INSERT INTO products ({names}) SELECT {names} FROM products_barcode_migration'))
                conn.execute(text("DROP TABLE products_barcode_migration"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_barcode ON products (barcode)"))
        transaction.commit()
        if engine.dialect.name == "sqlite":
            conn.execute(text("PRAGMA legacy_alter_table=OFF"))
            conn.execute(text("PRAGMA foreign_keys=ON"))

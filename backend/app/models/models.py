from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("QualityReport", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    profile_type: Mapped[str] = mapped_column(String(40), default="Custom")
    icon: Mapped[str] = mapped_column(String(16), default="👤")
    sodium_mg: Mapped[float | None] = mapped_column(Float, nullable=True, default=600)
    sugar_g: Mapped[float | None] = mapped_column(Float, nullable=True, default=10)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    user = relationship("User", back_populates="profiles")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    barcode: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    code_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(120))
    manufacturer: Mapped[str] = mapped_column(String(180))
    fssai: Mapped[str] = mapped_column(String(80), default="Not verified")
    fssai_license: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fssai_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fssai_source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fssai_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    evidence_status: Mapped[str] = mapped_column(String(30), default="UNCLEAR")
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    marketer: Mapped[str | None] = mapped_column(String(180), nullable=True)
    image: Mapped[str] = mapped_column(String(500), default="🍽️")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nutrition = relationship("Nutrition", back_populates="product", uselist=False, cascade="all, delete-orphan")
    ingredients = relationship("Ingredient", back_populates="product", cascade="all, delete-orphan")
    allergens = relationship("Allergen", back_populates="product", cascade="all, delete-orphan")
    regulatory_records = relationship("RegulatoryRecord", back_populates="product", cascade="all, delete-orphan")
    quality_reports = relationship("QualityReport", back_populates="product", foreign_keys="QualityReport.product_id")

class Nutrition(Base):
    __tablename__ = "nutrition"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), unique=True)
    sodium: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    sat_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    added_sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber: Mapped[float | None] = mapped_column(Float, nullable=True)
    serving_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    serving_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    product = relationship("Product", back_populates="nutrition")

class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    normalized_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    function: Mapped[str | None] = mapped_column(String(120), nullable=True)
    additive_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="green")
    note: Mapped[str] = mapped_column(Text, default="Declared on the label.")
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    product = relationship("Product", back_populates="ingredients")

class Allergen(Base):
    __tablename__ = "allergens"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    product = relationship("Product", back_populates="allergens")

class RegulatoryRecord(Base):
    __tablename__ = "regulatory_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="NOT_LOADED")
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str | None] = mapped_column(String(250), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    product = relationship("Product", back_populates="regulatory_records")

class QualityReport(Base):
    __tablename__ = "quality_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="reports")
    product = relationship("Product", back_populates="quality_reports", foreign_keys=[product_id])

class DartCheck(Base):
    __tablename__ = "dart_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    food: Mapped[str] = mapped_column(String(100), index=True)
    adulterant: Mapped[str] = mapped_column(String(180))
    title: Mapped[str] = mapped_column(String(250))
    steps: Mapped[list] = mapped_column(JSON)
    expected_observation: Mapped[str] = mapped_column(Text)
    caution: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120), default="FSSAI DART")
    source_url: Mapped[str] = mapped_column(String(500))

class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    captured_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sahi_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="UNCLEAR")
    verdict: Mapped[str] = mapped_column(String(30), default="UNCLEAR")
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="scans")
    product = relationship("Product")
    profile = relationship("Profile")

class Favorite(Base):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="favorites")
    __table_args__ = (UniqueConstraint("user_id", "scan_id", name="uq_user_scan_favorite"),)

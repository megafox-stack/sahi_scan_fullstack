from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import User, Profile, Product, Nutrition, Ingredient, Allergen, RegulatoryRecord, DartCheck
from app.core.security import hash_password
FSSAI_DART="https://www.fssai.gov.in/upload/knowledge_hub/1878035b34b558a3b48DART%20Book.pdf"

def seed_database():
    db:Session=SessionLocal()
    try:
        # Remove demo product seed and demo user creation.
        # Production seed should not insert fake products or demo accounts.
        if db.query(DartCheck).count()==0:
            checks=[("Milk","Water","Milk – added water",["Place a small quantity of milk on a clean, polished sloping surface.","Observe the flow and residue."],"Follow the official DART observation guidance.","Household screening only; not laboratory confirmation."),("Milk","Detergent","Milk – detergent",["Mix the sample with an equal quantity of water.","Shake and observe persistent froth."],"Persistent dense froth can be a warning sign.","Do not taste samples during testing."),("Milk","Starch","Milk – starch",["Follow the iodine-based DART procedure from the official booklet.","Observe any characteristic colour change."],"A characteristic colour change indicates possible starch.","Use the official procedure and appropriate precautions."),("Chilli powder","Brick powder / earthy material","Chilli powder – added brick or earthy material",["Place a small sample in water.","Observe settling and colour behaviour."],"Unusual heavy earthy material can be a warning sign.","Household screening only; not laboratory confirmation.")]
            db.add_all([DartCheck(food=f,adulterant=a,title=t,steps=s,expected_observation=o,caution=c,source="FSSAI DART",source_url=FSSAI_DART) for f,a,t,s,o,c in checks])
        db.commit()
    finally: db.close()

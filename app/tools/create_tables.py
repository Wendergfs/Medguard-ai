from app.core.database import Base, engine

# Import models so SQLAlchemy registers them
from app.models import (
    Medication,
    EvidencePassage,
    MedicationMention
)

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
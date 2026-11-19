
from sqlalchemy import Column, String, Text
from app.core.database import Base


class Medication(Base):
    __tablename__ = "medications"

    rxcui = Column(String(30), primary_key=True)
    preferred_name = Column(Text, nullable=False)

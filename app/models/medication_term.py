
from sqlalchemy import (
    Column, BigInteger, String, Text, Boolean,
    ForeignKey, UniqueConstraint
)
from app.core.database import Base


class MedicationTerm(Base):
    __tablename__ = "medication_terms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    rxcui = Column(
        String(30),
        ForeignKey("medications.rxcui"),
        nullable=False,
        index=True
    )

    name = Column(Text, nullable=False)
    term_type = Column(String(20))
    source = Column(String(50))
    term_status = Column(String(30))
    is_preferred = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint(
            "rxcui",
            "name",
            "term_type",
            "source",
            name="uq_medication_term"
        ),
    )


from sqlalchemy import (
    Column, BigInteger, String, Text,
    ForeignKey, Integer, UniqueConstraint
)
from app.core.database import Base


class MedicationMention(Base):
    __tablename__ = "medication_mentions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    passage_id = Column(
        BigInteger,
        ForeignKey("evidence_passages.id"),
        nullable=False
    )

    rxcui = Column(
        String(30),
        ForeignKey("medications.rxcui"),
        nullable=False
    )

    matched_text = Column(Text, nullable=False)

    start = Column(Integer)
    end = Column(Integer)

    term_type = Column(String(20))
    match_status = Column(String(30))

    __table_args__ = (
        UniqueConstraint(
            "passage_id",
            "rxcui",
            "matched_text",
            "start",
            "end",
            name="uq_medication_mention"
        ),
    )

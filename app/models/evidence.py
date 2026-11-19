
from sqlalchemy import (
    Column, BigInteger, Text, String,
    JSON, UniqueConstraint
)
from app.core.database import Base


class EvidencePassage(Base):
    __tablename__ = "evidence_passages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    source_record_id = Column(Text, nullable=False)
    effective_time = Column(String(30))
    version = Column(String(50))

    source_text = Column(Text, nullable=False)
    extraction_status = Column(
        String(30),
        default="unreviewed"
    )

    source_metadata = Column(JSON)

    __table_args__ = (
        UniqueConstraint(
            "source_record_id",
            "effective_time",
            name="uq_evidence_source_version"
        ),
    )

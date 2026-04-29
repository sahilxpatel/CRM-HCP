from sqlalchemy import Column, Date, DateTime, Integer, String, Text, func

from app.database.db import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=False)
    interaction_type = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

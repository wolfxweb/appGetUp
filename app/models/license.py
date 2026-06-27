from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    activation_key = Column(String(8), unique=True, index=True)
    status = Column(String(20), default="Disponível")  # "Disponível" ou "Utilizada"
    activation_date = Column(DateTime, nullable=True)
    activation_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    partner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    client_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    partner = relationship("User", foreign_keys=[partner_id])
    client_user = relationship("User", foreign_keys=[client_user_id])

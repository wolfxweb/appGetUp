from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base


class CustoFixo(Base):
    __tablename__ = "custo_fixo"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    valor = Column(Float, nullable=False)
    categoria = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="custo_fixo")
    
    def __repr__(self):
        return f"<CustoFixo(id={self.id}, nome={self.nome}, valor={self.valor}, user_id={self.user_id})>"
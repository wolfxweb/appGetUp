from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class Categoria(Base):
    __tablename__ = "categorias"
    
    codigo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String, nullable=False)
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento
    user = relationship("User", back_populates="categorias")
    produtos = relationship("Produto", back_populates="categoria", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Categoria(codigo={self.codigo}, nome={self.nome}, user_id={self.user_id})>"


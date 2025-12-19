from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class EventoVenda(Base):
    __tablename__ = "evento_venda"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nome_evento = Column(String, nullable=False)
    
    # Campos booleanos para tipo de impacto
    aumenta_vendas = Column(Boolean, default=False)  # Checkbox AUMENTAM
    diminui_vendas = Column(Boolean, default=False)  # Checkbox DIMINUEM
    
    # Meses afetados (array de meses 1-12)
    meses_afetados = Column(String, nullable=True)  # JSON string com array de meses marcados [1, 2, 3, ...]
    
    is_padrao = Column(Boolean, default=False)  # Se é evento pré-carregado
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento
    user = relationship("User", back_populates="eventos_venda")
    
    def __repr__(self):
        return f"<EventoVenda(id={self.id}, nome_evento={self.nome_evento}, user_id={self.user_id})>"


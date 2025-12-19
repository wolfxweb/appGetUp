from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class MesImportancia(Base):
    __tablename__ = "mes_importancia"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    
    # Campos editáveis e calculados
    nota_atribuida = Column(Float, nullable=True)  # Campo editável
    ritmo_negocio_percentual = Column(Float, nullable=True)  # Campo calculado
    quantidade_vendas_real = Column(Float, nullable=True)  # Do basic_data
    quantidade_vendas_estimada = Column(Float, nullable=True)  # Projeção
    peso_mes = Column(Float, nullable=True)  # Calculado no salvar
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento
    user = relationship("User", back_populates="meses_importancia")
    
    def __repr__(self):
        return f"<MesImportancia(id={self.id}, user_id={self.user_id}, year={self.year}, month={self.month})>"


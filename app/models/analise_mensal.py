from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base


class AnaliseMensal(Base):
    __tablename__ = "analise_mensal"
    __table_args__ = (
        UniqueConstraint('user_id', 'mes', 'ano', name='uq_analise_mensal_user_mes_ano'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mes = Column(Integer, nullable=False)  # 1-12
    ano = Column(Integer, nullable=False, index=True)
    
    # Dados de entrada (Step 2-4 do wizard)
    capacidade_atendimento = Column(Float, nullable=True)
    faturamento = Column(Float, nullable=True)
    quant_clientes = Column(Integer, nullable=True)
    gastos_vendas = Column(Float, nullable=True)
    custo_mercadorias = Column(Float, nullable=True)
    custo_fixo_total = Column(Float, nullable=True)
    
    # Campos calculados (Step 5 - resultados)
    ticket_medio = Column(Float, nullable=True)
    margem_bruta = Column(Float, nullable=True)
    ponto_equilibrio = Column(Float, nullable=True)
    margem_seguranca = Column(Float, nullable=True)
    custo_total = Column(Float, nullable=True)
    resultado = Column(Float, nullable=True)
    percentual_margem = Column(Float, nullable=True)
    
    # Correspondencia com caixa
    corresponde_caixa = Column(Boolean, nullable=True)
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="analises_mensais")
    
    def __repr__(self):
        return f"<AnaliseMensal(id={self.id}, user_id={self.user_id}, mes={self.mes}, ano={self.ano})>"

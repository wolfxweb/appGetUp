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
    
    # Slide 2 — Clientes e capacidade
    quant_clientes = Column(Integer, nullable=True)
    capacidade_atendimento = Column(Float, nullable=True)

    # Slide 3 — Faturamento
    faturamento = Column(Float, nullable=True)

    # Slide 4 — Gastos com vendas
    gastos_vendas = Column(Float, nullable=True)

    # Slide 5 — Custo das mercadorias
    custo_mercadorias = Column(Float, nullable=True)

    # Slide 6 — Custo fixo total
    custo_fixo_total = Column(Float, nullable=True)

    # Slides 3-7 — Campos calculados
    ticket_medio = Column(Float, nullable=True)               # faturamento / quant_clientes
    margem_bruta = Column(Float, nullable=True)               # faturamento - gastos_vendas - custo_mercadorias
    margem_contribuicao_por_cliente = Column(Float, nullable=True)  # margem_bruta / quant_clientes
    ponto_equilibrio = Column(Float, nullable=True)           # custo_fixo_total * faturamento / margem_bruta  (R$)
    margem_seguranca = Column(Float, nullable=True)           # (faturamento - ponto_equilibrio) / faturamento * 100
    custo_total = Column(Float, nullable=True)                # gastos_vendas + custo_mercadorias + custo_fixo_total
    resultado = Column(Float, nullable=True)                  # faturamento - custo_total
    percentual_margem = Column(Float, nullable=True)          # resultado / faturamento * 100

    # Slide 8 — Avaliação
    corresponde_caixa = Column(Boolean, nullable=True)
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="analises_mensais")
    
    def __repr__(self):
        return f"<AnaliseMensal(id={self.id}, user_id={self.user_id}, mes={self.mes}, ano={self.ano})>"

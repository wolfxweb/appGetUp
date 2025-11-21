from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class Produto(Base):
    __tablename__ = "produtos"
    
    codigo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nome = Column(String, nullable=False)
    categoria_codigo = Column(Integer, ForeignKey("categorias.codigo", ondelete="SET NULL"), nullable=True, index=True)
    basic_data_id = Column(Integer, ForeignKey("basic_data.id", ondelete="SET NULL"), nullable=True, index=True)  # ID dos dados básicos
    
    # Campos financeiros
    faturamento_por_mercadoria = Column(Float, nullable=True)
    preco_venda = Column(Float, nullable=True)
    custo_aquisicao = Column(Float, nullable=True)
    percentual_faturamento = Column(Float, nullable=True)  # % que o produto representa no faturamento
    quantidade_vendas = Column(Float, nullable=True)
    gastos_com_vendas = Column(Float, nullable=True)
    gastos_com_compras = Column(Float, nullable=True)
    
    # Margens
    margem_contribuicao_informada = Column(Float, nullable=True)  # %
    margem_contribuicao_corrigida = Column(Float, nullable=True)  # %
    margem_contribuicao_valor = Column(Float, nullable=True)  # R$
    
    # Análises
    custos_fixos = Column(Float, nullable=True)
    ponto_equilibrio = Column(Float, nullable=True)
    margem_operacional = Column(Float, nullable=True)
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="produtos")
    categoria = relationship("Categoria", back_populates="produtos")
    
    def __repr__(self):
        return f"<Produto(codigo={self.codigo}, nome={self.nome}, user_id={self.user_id})>"


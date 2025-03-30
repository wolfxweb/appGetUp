from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base
from app.models.basic_data_log import BasicDataLog

class BasicData(Base):
    __tablename__ = "basic_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    activity_type = Column(String, nullable=False)
    clients_served = Column(Integer, nullable=False)
    sales_revenue = Column(Float, nullable=False)
    sales_expenses = Column(Float, nullable=False)
    input_product_expenses = Column(Float, nullable=False)
    
    # Campos específicos para Comércio e Indústria
    fixed_costs = Column(Float, nullable=True)
    ideal_profit_margin = Column(Float, nullable=True)
    service_capacity = Column(String, nullable=True)
    
    # Campos específicos para Serviços
    pro_labore = Column(Float, nullable=True)
    work_hours_per_week = Column(Float, nullable=True)
    
    # Novos campos para Serviços
    other_fixed_costs = Column(Float, nullable=True)
    ideal_service_profit_margin = Column(Float, nullable=True)
    
    # Campo para indicar se é o registro atual
    is_current = Column(Boolean, nullable=True)
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamento
    user = relationship("User", back_populates="basic_data")
    logs = relationship("BasicDataLog", back_populates="basic_data", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BasicData(user_id={self.user_id}, month={self.month}, year={self.year}, activity_type={self.activity_type})>" 
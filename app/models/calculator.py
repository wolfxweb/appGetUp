from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class Calculator(Base):
    __tablename__ = "calculator"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    basic_data_id = Column(Integer, ForeignKey("basic_data.id", ondelete="CASCADE"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    current_margin = Column(Float, nullable=False)
    company_margin = Column(Float, nullable=False)
    desired_margin = Column(Float, nullable=False)
    suggested_price = Column(Float, nullable=False)
    price_relation = Column(Float, nullable=False)
    competitor_price = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Campos de controle
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user = relationship("User", back_populates="calculator_records")
    basic_data = relationship("BasicData", back_populates="calculator_records")
    
    def __repr__(self):
        return f"<Calculator(id={self.id}, product_name={self.product_name})>" 
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    whatsapp = Column(String)
    activity_type = Column(String, nullable=False) # Serviços, Comércio ou Indústria
    password = Column(String, nullable=False)
    activation_key = Column(String, nullable=True)
    activation_date = Column(DateTime, nullable=True)
    registration_date = Column(DateTime, default=datetime.now)
    status = Column(String, default="Ativo")
    access_level = Column(String, default="Cliente")
    terms_accepted = Column(Boolean, default=False)
    
    # Relacionamento com Dados Básicos
    basic_data = relationship("BasicData", back_populates="user", cascade="all, delete-orphan")
    
    # Relacionamento com registros da Calculadora
    calculator_records = relationship("Calculator", back_populates="user", cascade="all, delete-orphan") 
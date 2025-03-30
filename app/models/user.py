from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from datetime import datetime
from app.database.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    whatsapp = Column(String)
    activity_type = Column(String) # Serviços, Comércio ou Indústria
    password = Column(String)
    activation_key = Column(String, nullable=True)
    registration_date = Column(DateTime, default=datetime.now)
    status = Column(String, default="Ativo")
    access_level = Column(String, default="Cliente")
    terms_accepted = Column(Boolean, default=False) 
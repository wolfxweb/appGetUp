# app/models/basic_data_log.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class BasicDataLog(Base):
    __tablename__ = 'basic_data_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    basic_data_id = Column(Integer, ForeignKey('basic_data.id', ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    change_description = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    basic_data = relationship("BasicData", back_populates="logs")
    user = relationship("User", back_populates="basic_data_logs")
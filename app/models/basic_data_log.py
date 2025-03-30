# app/models/basic_data_log.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base

class BasicDataLog(Base):
    __tablename__ = 'basic_data_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    basic_data_id = Column(Integer, ForeignKey('basic_data.id', ondelete="CASCADE"))
    change_description = Column(String)
    
    basic_data = relationship("BasicData", back_populates="logs")
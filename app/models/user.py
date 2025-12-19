from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base
from app.models.basic_data_log import BasicDataLog

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    whatsapp = Column(String)
    activity_type = Column(String, nullable=False) # Serviços, Comércio ou Indústria
    password = Column(String, nullable=False)
    activation_key = Column(String, nullable=True)
    activation_date = Column(DateTime, nullable=True)
    registration_date = Column(DateTime, default=datetime.now)
    status = Column(String, default="Ativo")
    access_level = Column(String, default="Cliente")
    terms_accepted = Column(Boolean, default=False)
    
    # Novos campos opcionais
    gender = Column(String, nullable=True)  # Masculino ou Feminino
    birth_day = Column(Integer, nullable=True)  # Dia do aniversário
    birth_month = Column(Integer, nullable=True)  # Mês do aniversário
    married = Column(String, nullable=True)  # Sim ou Não
    children = Column(String, nullable=True)  # Sim ou Não
    grandchildren = Column(String, nullable=True)  # Sim ou Não
    cep = Column(String, nullable=True)  # CEP
    street = Column(String, nullable=True)  # Logradouro
    neighborhood = Column(String, nullable=True)  # Bairro
    state = Column(String, nullable=True)  # Estado (UF)
    city = Column(String, nullable=True)  # Cidade
    complement = Column(String, nullable=True)  # Complemento
    company_activity = Column(String, nullable=True)  # Atividade da Empresa
    specialty_area = Column(String, nullable=True)  # Área de Especialidade
    
    # Relacionamento com Dados Básicos
    basic_data = relationship("BasicData", back_populates="user", cascade="all, delete-orphan")
    # basic_data_logs = relationship("BasicDataLog", back_populates="user", cascade="all, delete-orphan")
    meses_importancia = relationship("MesImportancia", back_populates="user", cascade="all, delete-orphan")
    eventos_venda = relationship("EventoVenda", back_populates="user", cascade="all, delete-orphan")
    
    # Relacionamento com registros da Calculadora
    calculator_records = relationship("Calculator", back_populates="user", cascade="all, delete-orphan")
    
    # Relacionamento com Categorias
    categorias = relationship("Categoria", back_populates="user", cascade="all, delete-orphan")
    
    # Relacionamento com Produtos
    produtos = relationship("Produto", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>" 
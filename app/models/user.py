from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, func, ForeignKey
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
    activity_type = Column(String, nullable=False) # Servicos, Comercio ou Industria
    password = Column(String, nullable=False)
    activation_key = Column(String, nullable=True)
    activation_date = Column(DateTime, nullable=True)
    registration_date = Column(DateTime, default=datetime.now)
    status = Column(String, default="Ativo")
    access_level = Column(String, default="Cliente")
    terms_accepted = Column(Boolean, default=False)

    # Novos campos opcionais
    gender = Column(String, nullable=True)
    birth_day = Column(Integer, nullable=True)
    birth_month = Column(Integer, nullable=True)
    married = Column(String, nullable=True)
    children = Column(String, nullable=True)
    grandchildren = Column(String, nullable=True)
    cep = Column(String, nullable=True)
    street = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    complement = Column(String, nullable=True)
    company_activity = Column(String, nullable=True)
    specialty_area = Column(String, nullable=True)

    # Pos-cadastro: perguntas da Ana (margem e capacidade) + flag de fluxo
    ideal_profit_margin = Column(Float, nullable=True)
    service_capacity = Column(Float, nullable=True)
    ja_acessou = Column(Boolean, nullable=True)
    onboarding_completed = Column(Boolean, default=False, nullable=True)

    # Campos de estimativa (tela de analise - step 3 do onboarding)
    production_hours = Column(Float, nullable=True)
    estimated_loss_percentage = Column(Float, nullable=True)
    has_product_sheet = Column(String, nullable=True)  # "Sim" ou "Nao"

    # Relacionamentos
    basic_data = relationship("BasicData", back_populates="user", cascade="all, delete-orphan")
    meses_importancia = relationship("MesImportancia", back_populates="user", cascade="all, delete-orphan")
    eventos_venda = relationship("EventoVenda", back_populates="user", cascade="all, delete-orphan")
    calculator_records = relationship("Calculator", back_populates="user", cascade="all, delete-orphan")
    categorias = relationship("Categoria", back_populates="user", cascade="all, delete-orphan")
    produtos = relationship("Produto", back_populates="user", cascade="all, delete-orphan")
    analises_mensais = relationship("AnaliseMensal", back_populates="user", cascade="all, delete-orphan")
    custo_fixo = relationship("CustoFixo", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

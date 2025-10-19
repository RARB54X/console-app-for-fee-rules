from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.connection import Base  

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    transactions = relationship("Transaction", back_populates="agent")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    origen = Column(String(10))
    destino = Column(String(10))
    monto_origen = Column(Float)
    monto_destino = Column(Float)
    fee_total = Column(Float)
    fee_maxi = Column(Float)
    fee_operacion = Column(Float)
    fee_proveedor = Column(Float)
    
    agent = relationship("Agent", back_populates="transactions")
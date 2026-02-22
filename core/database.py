from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Creates a local SQLite database file instead of Excel
engine = create_engine('sqlite:///portfolio.db', connect_args={'timeout': 15})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class PortfolioItem(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    cost = Column(Float)
    quantity = Column(Float)
    status = Column(String, default="Open")
    date_added = Column(DateTime, default=datetime.utcnow)

# Create the tables
Base.metadata.create_all(bind=engine)
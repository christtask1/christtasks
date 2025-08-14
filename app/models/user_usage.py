from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

Base = declarative_base()

class UserUsage(Base):
    __tablename__ = "user_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    daily_message_count = Column(Integer, default=0)
    monthly_message_count = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserUsage(user_id={self.user_id}, daily_count={self.daily_message_count})>"

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot_usage.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create database tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

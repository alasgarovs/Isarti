from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, Float, Enum, DateTime, Date, ForeignKey, func, case, text, desc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import os

# Create base once
Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    password = Column(String(20), nullable=False)

class Barcodes(Base):
    __tablename__ = 'barcodes'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    count = Column(Integer, default=1)
    workspace_id = Column(Integer, nullable=False)

class WorkSpaces(Base):
    __tablename__ = 'workspaces'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    created_date = Column(Date, default=date.today)
    user = Column(String(50), nullable=False) 


# Create a SQLite database
engine = create_engine('sqlite:///local.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

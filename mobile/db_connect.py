from sqlalchemy import create_engine, Column, Integer, String, Date, desc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date


Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    password = Column(String(20), nullable=False)

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    device_name = Column(String(20), default='Guest')
    server_ip = Column(String(20), default='255.255.255.255')
    port_number = Column(String(20), default=3344)
    theme = Column(String(20), default='Light')
    current_user = Column(String(20), default='Guest')
    is_logged_in = Column(Integer, default=0)
    current_workspace_id = Column(String(20), default=0)

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

db_uri = 'sqlite:///local.db'
engine = create_engine(db_uri)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

session = Session()
try:
    settings = session.query(Settings).first()
    if not settings:
        settings = Settings(theme='Light', is_logged_in=0)
        session.add(settings)
        session.commit()

    user = session.query(Users).first()
    if not user:
        default_user = Users(username='root', password='toor')
        session.add(default_user)
        session.commit()

finally:
    session.close()

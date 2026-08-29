from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float,Text, ForeignKey

Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    symbol = Column(String)
    time_slot   = Column(String)
    approach    = Column(String)
    entry_model = Column(String)
    r_gain      = Column(Float)
    size        = Column(Float)
    time_to_tp  = Column(Integer)
    time_to_sl  = Column(Integer)

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date        = Column(String)
    time_slot   = Column(String)
    pregame     = Column(Text)
    checkin     = Column(Text)
    post_review = Column(Text)

class Reflection(Base):
    __tablename__ = "reflections"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(String, unique=True)
    reflection = Column(Text)

class Symbol(Base):
    __tablename__ = "symbols"

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)

class TimeSlot(Base):
    __tablename__ = "time_slots"

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)

class Approach(Base):
    __tablename__="approaches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(Text)
    entry_models = relationship("EntryModel", back_populates="approach", cascade="all, delete-orphan")

class EntryModel(Base):
    __tablename__="entry_models"
    id=Column(Integer, primary_key=True, autoincrement=True)
    name=Column(String)
    description = Column(Text)
    approach_name = Column(String, ForeignKey("approaches.name"))
    approach = relationship("Approach", back_populates="entry_models")

class Settings(Base):
    __tablename__="settings"
    key = Column(String, primary_key=True)
    value = Column(String)
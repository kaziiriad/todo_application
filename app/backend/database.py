from sqlalchemy import Boolean, create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timezone
import os
import secrets
from typing import Generator
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'myuser')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'mypassword')
DB_NAME = os.getenv('DB_NAME', 'mydb')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

Base = declarative_base()

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
except SQLAlchemyError as e:
    print(f"Error connecting to the database: {e}")
    raise

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Room(Base):
    """
    Room model for storing room information in the database.
    """
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, unique=True)
    description = Column(String, nullable=True)
    invite_code = Column(String, index=True, unique=True)
    creator_email = Column(String)
    participant_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Using UTC timezone
    participants = relationship("RoomParticipant", back_populates="room")
    tasks = relationship("Task", back_populates="room")

    def remove_participant(self, participant_email: str):
        """
        Remove a participant from the room.
        
        Args:
            participant_email: The email of the participant to remove
        """
        participant = self.participants.filter_by(email=participant_email).first()
        if participant:
            self.participants.remove(participant)
            self.participant_count -= 1
            self.save()
    def add_participant(self, participant_email: str):
        
        participant = self.participants.filter_by(email=participant_email).first()
        if not participant:
            self.participants.append(RoomParticipant(email=participant_email))
            self.participant_count += 1
            
    def create_invite_code(self):
        self.invite_code = secrets.token_urlsafe(8)
    def remove_room(self):
        """
        Remove the room from the database.
        """
        

class RoomParticipant(Base):
    __tablename__ = 'room_participants'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    email = Column(String, index=True)
    room = relationship("Room", back_populates="participants")

    def email_validation(self):
        # Add email validation logic here
        pass
    
    
class Task(Base):
    """
    Task model for storing task information in the database.
    """
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Using UTC timezone
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    room = relationship("Room", back_populates="tasks")

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()
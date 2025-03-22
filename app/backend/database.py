from sqlalchemy import Boolean, create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timezone, timedelta
import os
import secrets
from typing import Generator, Optional
from sqlalchemy.exc import SQLAlchemyError
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'myuser')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'mypassword')
DB_NAME = os.getenv('DB_NAME', 'mydb')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

Base = declarative_base()

# Retry logic for database connection
def get_engine(max_retries=5, retry_interval=5):
    """
    Create a database engine with retry logic
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Time in seconds between retries
        
    Returns:
        SQLAlchemy engine
    """
    retries = 0
    last_exception = None
    
    while retries < max_retries:
        try:
            logger.info(f"Attempting to connect to database (attempt {retries+1}/{max_retries})...")
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            # Test the connection
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.info("Database connection successful!")
            return engine
        except SQLAlchemyError as e:
            last_exception = e
            logger.warning(f"Database connection failed: {e}")
            retries += 1
            if retries < max_retries:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
    
    logger.error(f"Failed to connect to database after {max_retries} attempts")
    raise last_exception

try:
    engine = get_engine()
except SQLAlchemyError as e:
    logger.error(f"Error connecting to the database: {e}")
    raise

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# User model for authentication
class User(Base):
    """
    User model for storing user information and authentication.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    rooms = relationship("Room", secondary="room_participants", back_populates="participants")
    
    @classmethod
    def get_or_create(cls, db: Session, email: str) -> "User":
        """
        Get an existing user or create a new one if not found.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User object
        """
        user = db.query(cls).filter(cls.email == email).first()
        if not user:
            user = cls(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def update_last_login(self, db: Session) -> None:
        """
        Update the user's last login timestamp.
        
        Args:
            db: Database session
        """
        self.last_login = datetime.now(timezone.utc)
        db.add(self)
        db.commit()

# Auth token model for magic link authentication
class AuthToken(Base):
    """
    AuthToken model for storing magic link tokens.
    """
    __tablename__ = 'auth_tokens'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="auth_tokens")
    
    @classmethod
    def create_token(cls, db: Session, user_id: int, expires_in_minutes: int = 15) -> "AuthToken":
        """
        Create a new authentication token for magic link.
        
        Args:
            db: Database session
            user_id: ID of the user
            expires_in_minutes: Token expiration time in minutes
            
        Returns:
            AuthToken object
        """
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        
        # Create token record
        auth_token = cls(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        
        db.add(auth_token)
        db.commit()
        db.refresh(auth_token)
        
        return auth_token
    
    @classmethod
    def validate_token(cls, db: Session, token: str) -> Optional[int]:
        """
        Validate a token and return the associated user ID if valid.
        
        Args:
            db: Database session
            token: Token string to validate
            
        Returns:
            User ID if token is valid, None otherwise
        """
        auth_token = db.query(cls).filter(
            cls.token == token,
            cls.is_used == False,
            cls.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if auth_token:
            # Mark token as used
            auth_token.is_used = True
            db.add(auth_token)
            db.commit()
            
            return auth_token.user_id
        
        return None

class Room(Base):
    """
    Room model for storing room information in the database.
    """
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, unique=True)
    description = Column(String, nullable=True)
    invite_code = Column(String, index=True, unique=True)
    creator_id = Column(Integer, ForeignKey('users.id'))  # Changed from creator_email to creator_id
    participant_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Using UTC timezone
    participants = relationship("User", secondary="room_participants", back_populates="rooms")
    # tasks = relationship("Task", back_populates="room")
    creator = relationship("User", foreign_keys=[creator_id])

    def remove_participant(self, participant_email: str, db: Session):
        """
        Remove a participant from the room.
        
        Args:
            participant_email: The email of the participant to remove
            db: SQLAlchemy database session
        """
        participant = db.query(RoomParticipant).filter_by(room_id=self.id, email=participant_email).first()
        if participant:
            db.delete(participant)
            self.participant_count -= 1
            db.add(self)
            db.commit()

    def add_participant(self, participant_email: str, db: Session):
        """
        Add a participant to the room.
        
        Args:
            participant_email: The email of the participant to add
            db: SQLAlchemy database session
        """
        participant = db.query(RoomParticipant).filter_by(room_id=self.id, email=participant_email).first()
        if not participant:
            new_participant = RoomParticipant(room_id=self.id, email=participant_email)
            db.add(new_participant)
            self.participant_count += 1
            db.add(self)
            db.commit()

    def create_invite_code(self, db: Session):
        """
        Create a unique invite code for this room.
        
        Args:
            db: SQLAlchemy database session
        """
        self.invite_code = secrets.token_urlsafe(8)
        db.add(self)
        db.commit()
        return self.invite_code
    @classmethod
    def remove_room(cls, room_id: int, db: Session):
        """
        Remove the room from the database.
        
        Args:
            room_id: The ID of the room to remove
            db: SQLAlchemy database session
            
        Returns:
            bool: True if the room was removed, False if it wasn't found
        """
        room = db.query(cls).filter(cls.id == room_id).first()
        if room:
            # Delete associated participants
            db.query(RoomParticipant).filter(RoomParticipant.room_id == room_id).delete()
            
            # Delete associated tasks
            db.query(Task).filter(Task.room_id == room_id).delete()
            
            # Delete the room
            db.delete(room)
            db.commit()
            return True
        return False
        

class RoomParticipant(Base):
    __tablename__ = 'room_participants'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    user_id = Column(Integer, ForeignKey('users.id'))  # Changed from email to user_id
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    role = Column(String, default='member')  # 'owner', 'admin', 'member'
    
    
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
    # room_id = Column(Integer, ForeignKey('rooms.id'), nullable=True)
    # user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Added user_id for task ownership
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Using UTC timezone
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # room = relationship("Room", back_populates="tasks")
    # user = relationship("User")  # Task owner

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

from typing import Optional, Union, List
from datetime import datetime
from pydantic import BaseModel, field_validator, EmailStr

class TaskModel(BaseModel):
    """Base model for task data with common fields."""
    title: str
    description: Optional[str] = None
    completed: bool = False
    due_date: Optional[datetime] = None


class TaskCreate(TaskModel):
    """Model for creating a new task, inherits all fields from TaskModel."""
    room_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Model for updating an existing task with all fields optional."""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskResponse(TaskModel):
    """Model for task response data including database fields."""
    id: int
    room_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]

    @field_validator('created_at', 'updated_at', mode='before')
    def parse_datetime(cls, value):
        """Convert datetime objects to ISO format strings."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    model_config = {"from_attributes": True}


class RoomJoinRequest(BaseModel):
    """Model for requesting to join a room."""
    invite_code: str


class RoomInviteRequest(BaseModel):
    """Model for inviting a participant to a room."""
    room_id: int
    email: EmailStr


class RoomCreate(BaseModel):
    """Model for creating a new room."""
    name: str
    description: Optional[str] = None


class RoomResponse(BaseModel):
    """Model for room response data including database fields."""
    id: int
    name: str
    invite_code: str
    creator_email: str
    participant_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomDetailResponse(RoomResponse):
    """Model for detailed room response including participants."""
    participants: List["UserResponse"] = []
    
    model_config = {"from_attributes": True}


# Authentication schemas
class MagicLinkRequest(BaseModel):
    """Model for requesting a magic link."""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response for magic link request."""
    message: str


class TokenVerifyRequest(BaseModel):
    """Model for verifying a magic link token."""
    token: str


class UserResponse(BaseModel):
    """Model for user response data."""
    id: int
    email: str
    display_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class CurrentUserResponse(UserResponse):
    """Model for current user response with additional data."""
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    """Model for session response data."""
    access_token: str
    token_type: str = "bearer"
    user: CurrentUserResponse

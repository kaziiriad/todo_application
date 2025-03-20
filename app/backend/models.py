from typing import Optional, Union
from pydantic import BaseModel, validator
from datetime import datetime

class TaskModel(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    due_date: Optional[datetime] = None

class TaskCreate(TaskModel):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskResponse(TaskModel):
    id: int
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]

    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    class Config:
        from_attributes = True

class RoomJoinRequest(BaseModel):
    invite_code: str
    participant_email: str

class RoomInviteRequest(BaseModel):
    room_id: int
    participant_email: str

class RoomCreate(BaseModel):
    name: str
    creator_email: str

class RoomResponse(BaseModel):
    id: int
    name: str
    invite_code: str
    creator_email: str
    participant_count: int
    created_at: datetime

    class Config:
        from_attributes = True

from typing import Optional
from pydantic import BaseModel
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
    created_at: datetime
    updated_at: datetime

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

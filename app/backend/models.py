from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class TaskModel(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    due_date: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

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
    pass

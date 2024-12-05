from fastapi import FastAPI, HTTPException, Depends, status
from typing import List
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from models import TaskCreate, TaskUpdate, TaskResponse
from database import Task, get_db, DATABASE_URL  # Assuming TaskBase is renamed to Task for clarity
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="TODO API",
    description="REST API for managing tasks",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get(
    "/tasks/", 
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tasks"
)
async def get_all_tasks(db: Session = Depends(get_db)):
    """
    Retrieve all tasks from the database.
    
    Returns:
        List[TaskResponse]: List of all tasks
    """
    tasks = db.query(Task).all()
    return tasks

@app.get(
    "/tasks/{task_id}", 
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific task"
)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific task by its ID.
    
    Args:
        task_id: The ID of the task to retrieve
        
    Raises:
        HTTPException: If task is not found
        
    Returns:
        TaskResponse: The requested task
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with ID {task_id} not found"
        )
    return task

@app.post(
    "/tasks/", 
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task"
)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task.
    
    Args:
        task: The task data to create
        
    Returns:
        TaskResponse: The created task
    """
    new_task = Task(**task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.patch(
    "/tasks/{task_id}", 
    response_model=TaskUpdate,
    status_code=status.HTTP_200_OK,
    summary="Update a task"
)
async def update_task(
    task_id: int, 
    task_update: TaskUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update a specific task.
    
    Args:
        task_id: The ID of the task to update
        task_update: The update data
        
    Raises:
        HTTPException: If task is not found
        
    Returns:
        TaskResponse: The updated task
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with ID {task_id} not found"
        )

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task"
)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific task.
    
    Args:
        task_id: The ID of the task to delete
        
    Raises:
        HTTPException: If task is not found
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with ID {task_id} not found"
        )
    
    db.delete(task)
    db.commit()



@app.get("/health", response_model=dict, status_code=status.HTTP_200_OK)
async def health():
    """
    Check the health of the application and database connection.
    
    Returns:
        dict: Health status of the application and database
    """
    health_status = {"status": "Healthy", "database": "Connected"}

    # Check if the database connection is active
    if not DATABASE_URL:
        health_status["database"] = "Database URL not set"
        return health_status
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()  # Actually execute the query
        health_status["database"] = "Connected"
    except SQLAlchemyError as e:
        health_status["status"] = "Unhealthy"
        health_status["database"] = f"Database connection error: {str(e)}"
    
    return health_status
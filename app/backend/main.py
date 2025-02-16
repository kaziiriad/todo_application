from collections import defaultdict
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi_socketio import SocketManager
from typing import List
from pydantic import EmailStr
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
# from mailer import send_invite_email
from models import RoomCreate, RoomResponse, TaskCreate, TaskUpdate, TaskResponse, RoomInviteRequest, RoomJoinRequest
from manager import RedisManager
from database import (
    Task,
    get_db,
    DATABASE_URL,
    Room,
    RoomParticipant,
)  # Assuming TaskBase is renamed to Task for clarity
from fastapi.middleware.cors import CORSMiddleware
import os
import socketio

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 0)

app = FastAPI(
    title="TODO API", description="REST API for managing tasks", version="1.0.0"
)

sio = SocketManager(app=app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

redis_manager = RedisManager(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


@app.get(
    "/tasks/",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tasks",
)
async def get_all_tasks(db: Session = Depends(get_db)):
    """
    Retrieve all tasks from the database.

    Returns:
        List[TaskResponse]: List of all tasks
    """
    redis_key = "tasks"
    cached_tasks = redis_manager.get(redis_key)
    if cached_tasks:
        return cached_tasks
    tasks = db.query(Task).all()
    redis_manager.set(redis_key, tasks, expire=600)  # Cache for 10 minutes
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific task",
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
    redis_key = f"task_{task_id}"
    cached_task = redis_manager.get(redis_key)
    if cached_task:
        return cached_task
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    redis_manager.set(redis_key, task, expire=300)
    return task


@app.post(
    "/tasks/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
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

    await sio.emit("task_created", TaskResponse.model_validate(new_task).model_dump())

    return new_task


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskUpdate,
    status_code=status.HTTP_200_OK,
    summary="Update a task",
)
async def update_task(
    task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)
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
            detail=f"Task with ID {task_id} not found",
        )

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)

    await sio.emit('task_updated', TaskResponse.model_validate(db_task).model_dump())


    return db_task


@app.delete(
    "/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task"
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
            detail=f"Task with ID {task_id} not found",
        )

    db.delete(task)
    db.commit()

    await sio.emit('task_deleted', {"task_id": task_id})



@app.get("/health", response_model=dict, status_code=status.HTTP_200_OK)
async def health():
    """
    Check the health of the application and database connection.

    Returns:
        dict: Health status of the application and database
    """
    health_status = defaultdict(str)
    # Check if the database connection is active

    if not DATABASE_URL:
        health_status["database"]["msg"] = "Database URL not set"
        return health_status

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()  # Actually execute the query
        health_status["database"]["status"] = "Connected"

    except SQLAlchemyError as e:
        health_status["database"]["status"] = "Unhealthy"
        health_status["database"]["msg"] = f"Database connection error: {str(e)}"

    try:
        redis_manager.ping()
        health_status["redis"]["status"] = "Connected"
    except Exception as e:
        health_status["redis"]["status"] = "Unhealthy"
        health_status["redis"]["msg"] = f"Redis connection error: {str(e)}"

    return health_status


@app.post("/rooms/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    """
    Create a new room with an invite code.
    
    Args:
        room: RoomCreate model containing room details
        
    Returns:
        RoomResponse: Created room details including the invite code
    """
    # Check if room name already exists
    existing_room = db.query(Room).filter(Room.name == room.name).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room with this name already exists"
        )
    
    # Create new room
    new_room = Room(
        name=room.name,
        creator_email=room.creator_email,
        participant_count=1  # Creator is the first participant
    )
    
    # Generate invite code
    new_room.create_invite_code()
    
    # Add creator as first participant
    initial_participant = RoomParticipant(
        email=room.creator_email
    )
    new_room.participants.append(initial_participant)
    
    try:
        db.add(new_room)
        db.commit()
        db.refresh(new_room)
        
        # Emit socket event for room creation
        await sio.emit('room_created', {
            'room_id': new_room.id,
            'room_name': new_room.name,
            'creator_email': new_room.creator_email
        })
        
        return new_room
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create room"
        )

@app.get("/rooms/{room_id}", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def get_room(room_id: int, db: Session = Depends(get_db)):
    """
    Get room details by ID.
    
    Args:
        room_id: ID of the room to retrieve
        
    Returns:
        RoomResponse: Room details
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    return room

@app.post("/rooms/join/", status_code=status.HTTP_200_OK)
async def join_room(join_request: RoomJoinRequest, db: Session = Depends(get_db)):
    """
    Join a room using an invite code.
    
    Args:
        join_request: Contains invite_code and participant_email
        
    Returns:
        dict: Room details and join confirmation
    """
    room = db.query(Room).filter(Room.invite_code == join_request.invite_code).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code or room not found"
        )
    
    # Check if participant already exists in the room
    existing_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == room.id,
        RoomParticipant.email == join_request.participant_email
    ).first()
    
    if existing_participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant in this room"
        )
    
    # Add participant to room
    new_participant = RoomParticipant(
        room_id=room.id,
        email=join_request.participant_email
    )
    db.add(new_participant)
    room.participant_count += 1
    
    try:
        db.commit()
        # Emit socket event to notify other participants
        await sio.emit('participant_joined', {
            'room_id': room.id,
            'participant_email': join_request.participant_email
        })
        
        return {
            "message": "Successfully joined the room",
            "room_name": room.name,
            "room_id": room.id
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join room"
        )

# @app.post("/rooms/invite", status_code=status.HTTP_200_OK)
# async def invite_to_room(invite_request: RoomInviteRequest, db: Session = Depends(get_db)):
#     """
#     Send an invitation to join a room.
    
#     Args:
#         invite_request: Contains room_id and participant_email
        
#     Returns:
#         dict: Invitation confirmation
#     """
#     room = db.query(Room).filter(Room.id == invite_request.room_id).first()
#     if not room:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Room not found"
#         )
    
#     # Create invite code if not exists
#     if not room.invite_code:
#         room.create_invite_code()
#         db.commit()
    
#     try:
#         # Send invitation email
#         await send_invite_email(
#             email=invite_request.participant_email,
#             room_name=room.name,
#             invite_code=room.invite_code
#         )
        
#         return {
#             "message": "Invitation sent successfully",
#             "invite_code": room.invite_code
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to send invitation"
#         )

@sio.on('connect')
async def handle_connect(sid, environ):
    """Handle client connection"""
    await sio.emit('connection_established', {
        "status": "connected",
        "sid": sid
    }, room=sid)


@sio.on('disconnect')
async def handle_disconnect(sid):
    """Handle client disconnection"""
    # Get user's active rooms and notify others
    rooms = sio.rooms(sid)
    for room in rooms:
        if room != sid:  # Don't process the user's personal room
            await sio.emit('user_disconnected', {
                "sid": sid
            }, room=room)

@sio.on('join_room')
async def handle_room_join(sid, data):
    """Handle real-time room joining"""
    room_id = data.get('room_id')
    if room_id:
        sio.enter_room(sid, f"room_{room_id}")
        await sio.emit('room_joined', {
            "room_id": room_id,
            "status": "connected"
        }, room=f"room_{room_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
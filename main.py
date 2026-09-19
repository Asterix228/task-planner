from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import DateTime, Enum as SAEnum, select, String, Text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from pydantic import BaseModel,ConfigDict
from enum import Enum
from datetime import datetime, timezone
from logger import write_log
import uuid
from webhook_client import notify_task_created,retry_worker

app = FastAPI()

engine = create_async_engine("sqlite+aiosqlite:///tasks.db")

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

@app.on_event("startup")
async def start_retry_worker():
    asyncio.create_task(retry_worker())
SessionDep = Annotated[AsyncSession,Depends(get_session)]

class Base(DeclarativeBase):
    pass

class TaskStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
 
class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status"),
        default=TaskStatus.new,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
class TaskUpdateSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None

@app.post("/setup_datebase")
async def setup_datebase():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"success": True}

class TaskAddSchema(BaseModel):
    title: str
    description: str
    
class TaskSchema(TaskAddSchema):
    id: int
    status: TaskStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@app.post("/tasks", response_model=TaskSchema,)
async def add_tasks(data: TaskAddSchema, session:SessionDep):
    new_task = taskModel(
        title=data.title,
        description=data.description,
    )
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    task_json = TaskSchema.model_validate(new_task).model_dump(mode="json")
    await write_log(task_json)
    return {"success": True}

@app.patch("/tasks/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: int,
    data: TaskUpdateSchema,
    session: SessionDep, 
):
    task = await session.get(TaskModel, task_id)
    if task is None:
        raise HTTPException(status_code = 404,detail="task not found")
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task,field,value)
    
    await session.commit()
    await session.refresh(task)
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, session: SessionDep):
    task = await session.get(TaskModel, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    await session.delete(task)
    await session.commit()
    return {"success": True}

@app.get("/tasks", response_model=list[TaskSchema])
async def get_tasks(session:SessionDep):
    query = select(TaskModel)
    result = await  session.execute(query)
    return result.scalars().all()

@app.get("/tasks/{task_id}", response_model=TaskSchema)
async def get_task(task_id: int, session: SessionDep):
    task = await session.get(TaskModel, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task
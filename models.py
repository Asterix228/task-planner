from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from uuid import UUID


class TaskStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"


class Task(BaseModel):
    id: UUID
    title: str
    description: str
    status: TaskStatus
    created_at: datetime

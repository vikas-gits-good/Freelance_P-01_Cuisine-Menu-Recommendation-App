from enum import Enum
from multiprocessing import Process
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskType(str, Enum):
    SEED = "seeder"
    SCRP = "scraper"
    LOAD = "loader"


class TaskStatus(str, Enum):
    IDLE = "idle"
    ONGOING = "ongoing"
    FINISHED = "finished"
    FAILED = "failed"
    ERROR = "error"
    KILLED = "killed"


class StatusMessage(BaseModel):
    status: TaskStatus = Field(
        default=TaskStatus.IDLE,  # Don't change it to ONGOING
        description="Status of current api call",
    )
    task: TaskType = Field(
        default=TaskType.SEED,
        description="Task name. seeder, scrapr or loader",
    )
    task_id: str = Field(
        default="",
        description="Hex UUID of api call",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional error or info message",
    )


class APIStatus(StatusMessage):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    process: Optional[Process] = Field(
        default=None,
        exclude=True,
        description="The programm that is running is accessed here",
    )

    def to_message(self) -> StatusMessage:
        """Convert to StatusMessage for safe serialization."""
        return StatusMessage(
            status=self.status,
            task=self.task,
            task_id=self.task_id,
            message=self.message,
        )

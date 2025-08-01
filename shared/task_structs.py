from dataclasses import dataclass
from enum import Enum
import datetime
from typing import Optional

class TaskStatus(Enum):
    """Enumeration for the status of a Task."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"

class TaskPriority(Enum):
    """Enumeration for the priority level of a Task."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

@dataclass
class Task:
    task_id: Optional[int] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    due_date: datetime.date | datetime.datetime | None = None
    status: TaskStatus = TaskStatus.OPEN
    priority: Optional[TaskPriority] = None
    assigned_to_user_id: Optional[int] = None
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("Task title cannot be empty.")
        if self.due_date is None:
            raise ValueError("Task due_date must be provided.")

    def __str__(self) -> str:
        return (
            f"Task ID: {self.task_id}\n"
            f"Title: {self.title}\n"
            f"Status: {self.status.value}\n"
            f"Priority: {self.priority.value if self.priority else 'N/A'}\n"
            f"Due Date: {self.due_date.isoformat() if self.due_date else 'N/A'}\n"
            f"Assigned To User ID: {self.assigned_to_user_id}\n"
            f"Created By User ID: {self.created_by_user_id}\n"
            f"Company ID: {self.company_id}\n"
            f"Contact ID: {self.contact_id}"
        )

    def to_dict(self) -> dict:
        """Returns the task as a dictionary."""
        return {
            "task_id": self.task_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "priority": self.priority.value if self.priority else None,
            "assigned_to_user_id": self.assigned_to_user_id,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Creates a Task object from a dictionary representation."""
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            try:
                due_date = datetime.datetime.fromisoformat(due_date)
            except ValueError:
                due_date = datetime.date.fromisoformat(due_date)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.datetime.fromisoformat(updated_at)

        return cls(
            task_id=data.get("task_id"),
            company_id=data.get("company_id"),
            contact_id=data.get("contact_id"),
            title=data.get("title", ""),
            description=data.get("description"),
            due_date=due_date,
            status=TaskStatus(data.get("status", "Open")) if data.get("status") else TaskStatus.OPEN,
            priority=TaskPriority(data.get("priority")) if data.get("priority") else None,
            assigned_to_user_id=data.get("assigned_to_user_id"),
            created_by_user_id=data.get("created_by_user_id"),
            created_at=created_at,
            updated_at=updated_at,
        )

from dataclasses import dataclass
from enum import Enum
import datetime
from typing import Optional

class InteractionType(Enum):
    CALL = "Call"
    EMAIL = "Email"
    MEETING = "Meeting"
    VISIT = "Visit"
    OTHER = "Other"

@dataclass
class Interaction:
    interaction_id: Optional[int] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    interaction_type: Optional[InteractionType] = None
    date_time: Optional[datetime.datetime] = None
    subject: str = ""
    description: str = ""
    created_by_user_id: Optional[int] = None
    attachment_path: str = ""

    def __str__(self) -> str:
        return (
            f"Interaction ID: {self.interaction_id}\n"
            f"Company ID: {self.company_id}\n"
            f"Contact ID: {self.contact_id}\n"
            f"Type: {self.interaction_type.value if self.interaction_type else 'N/A'}\n"
            f"Date/Time: {self.date_time.isoformat() if self.date_time else 'N/A'}\n"
            f"Subject: {self.subject}\n"
            f"Description: {self.description}\n"
            f"Created By User ID: {self.created_by_user_id}\n"
            f"Attachment Path: {self.attachment_path}"
        )

    def to_dict(self) -> dict:
        """Returns the interaction as a dictionary."""
        return {
            "interaction_id": self.interaction_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "interaction_type": self.interaction_type.value if self.interaction_type else None,
            "date_time": self.date_time.isoformat() if self.date_time else None,
            "subject": self.subject,
            "description": self.description,
            "created_by_user_id": self.created_by_user_id,
            "attachment_path": self.attachment_path,
        }

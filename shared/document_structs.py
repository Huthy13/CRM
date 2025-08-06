from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class AccountDocument:
    document_id: Optional[int] = None
    account_id: Optional[int] = None
    document_type: str = ""
    file_path: str = ""
    uploaded_at: Optional[datetime.datetime] = None
    expires_at: Optional[datetime.datetime] = None

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "account_id": self.account_id,
            "document_type": self.document_type,
            "file_path": self.file_path,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def __str__(self) -> str:
        return (
            f"Document ID: {self.document_id}\n"
            f"Account ID: {self.account_id}\n"
            f"Type: {self.document_type}\n"
            f"File Path: {self.file_path}\n"
            f"Uploaded At: {self.uploaded_at.isoformat() if self.uploaded_at else 'N/A'}\n"
            f"Expires At: {self.expires_at.isoformat() if self.expires_at else 'N/A'}"
        )


"""Shared data structures and utilities for the CRM project."""

from .account_structs import AccountType, Address, Account, Contact
from .interaction_structs import InteractionType, Interaction
from .task_structs import TaskStatus, TaskPriority, Task
from .document_structs import AccountDocument
from .structs import *  # Re-export remaining legacy structures

__all__ = [
    "AccountType", "Address", "Account", "Contact",
    "InteractionType", "Interaction",
    "TaskStatus", "TaskPriority", "Task",
    "AccountDocument",
]

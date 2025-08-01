import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create the tasks table and trigger."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            contact_id INTEGER,
            title VARCHAR(150) NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT,
            assigned_to_user_id INTEGER,
            created_by_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            FOREIGN KEY (company_id) REFERENCES accounts (id) ON DELETE SET NULL,
            FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_to_user_id) REFERENCES users (user_id) ON DELETE SET NULL,
            FOREIGN KEY (created_by_user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
        AFTER UPDATE ON tasks
        FOR EACH ROW
        WHEN OLD.updated_at = NEW.updated_at
        BEGIN
            UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE task_id = OLD.task_id;
        END;
    """)

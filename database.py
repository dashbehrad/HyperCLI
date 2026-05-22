"""
HyperCLI Database Module
========================
This module handles all database operations for the HyperCLI application.
It provides persistent storage for conversation history, project metadata,
and user preferences using SQLite.

Author: HyperCLI Development Team
Version: 1.0.0
"""

import sqlite3
import json
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

from config import config


class DatabaseManager:
    """
    Database manager for HyperCLI application.
    
    This class provides a thread-safe interface for all database operations,
    including conversation history storage, project metadata management,
    and user preference persistence.
    
    Attributes:
        db_path (Path): Path to the SQLite database file.
        connection (sqlite3.Connection): Active database connection.
        lock (threading.Lock): Thread lock for safe concurrent access.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path (Optional[Path]): Path to the database file. 
                                     Defaults to config.DATABASE_PATH.
        """
        self.db_path = db_path or config.DATABASE_PATH
        self.lock = threading.Lock()
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: A database connection object.
            
        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects")
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=config.DB_TIMEOUT,
            check_same_thread=False
        )
        
        # Enable WAL mode for better concurrent access if configured
        if config.DB_WAL_MODE:
            conn.execute("PRAGMA journal_mode=WAL")
        
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_database(self) -> None:
        """
        Initialize the database schema if it doesn't exist.
        
        Creates all necessary tables for storing:
        - Projects metadata
        - Conversation history
        - File operation logs
        - User preferences
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    path TEXT NOT NULL,
                    language TEXT,
                    framework TEXT,
                    is_active BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Create file_operations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    operation_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Create user_preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_project_id 
                ON conversations(project_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                ON conversations(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_operations_project_id 
                ON file_operations(project_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_name 
                ON projects(name)
            """)
            
            conn.commit()
    
    # ==================== PROJECT OPERATIONS ====================
    
    def create_project(
        self,
        name: str,
        description: str = "",
        language: str = "",
        framework: str = ""
    ) -> int:
        """
        Create a new project in the database.
        
        Args:
            name (str): Project name.
            description (str): Project description.
            language (str): Primary programming language.
            framework (str): Framework used.
            
        Returns:
            int: The ID of the newly created project.
            
        Raises:
            sqlite3.IntegrityError: If a project with the same name exists.
        """
        project_path = str(config.PROJECTS_DIR / name)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (name, description, path, language, framework)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, project_path, language, framework))
            conn.commit()
            return cursor.lastrowid
    
    def get_project(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get project details by name.
        
        Args:
            name (str): Project name.
            
        Returns:
            Optional[Dict[str, Any]]: Project details as a dictionary, 
                                     or None if not found.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects from the database.
        
        Returns:
            List[Dict[str, Any]]: List of all projects.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects ORDER BY updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active project.
        
        Returns:
            Optional[Dict[str, Any]]: Active project details or None.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects WHERE is_active = TRUE LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def set_active_project(self, name: str) -> bool:
        """
        Set a project as the active project.
        
        Args:
            name (str): Project name to set as active.
            
        Returns:
            bool: True if successful, False if project not found.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Deactivate all projects first
            cursor.execute("UPDATE projects SET is_active = FALSE")
            
            # Activate the specified project
            cursor.execute("""
                UPDATE projects SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (name,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def update_project(self, name: str, **kwargs) -> bool:
        """
        Update project details.
        
        Args:
            name (str): Project name to update.
            **kwargs: Fields to update (description, language, framework).
            
        Returns:
            bool: True if successful, False if project not found.
        """
        if not kwargs:
            return False
        
        # Build dynamic update query
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['description', 'language', 'framework']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(name)
        
        query = f"UPDATE projects SET {', '.join(fields)} WHERE name = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_project(self, name: str) -> bool:
        """
        Delete a project from the database.
        
        Args:
            name (str): Project name to delete.
            
        Returns:
            bool: True if successful, False if project not found.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== CONVERSATION OPERATIONS ====================
    
    def add_message(
        self,
        role: str,
        content: str,
        project_name: Optional[str] = None
    ) -> int:
        """
        Add a message to the conversation history.
        
        Args:
            role (str): Message role ('user' or 'assistant').
            content (str): Message content.
            project_name (Optional[str]): Associated project name.
            
        Returns:
            int: ID of the inserted message.
        """
        project_id = None
        if project_name:
            project = self.get_project(project_name)
            if project:
                project_id = project['id']
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (project_id, role, content)
                VALUES (?, ?, ?)
            """, (project_id, role, content))
            conn.commit()
            return cursor.lastrowid
    
    def get_conversation_history(
        self,
        project_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            project_name (Optional[str]): Filter by project name.
            limit (int): Maximum number of messages to retrieve.
            
        Returns:
            List[Dict[str, Any]]: List of conversation messages.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if project_name:
                project = self.get_project(project_name)
                if project:
                    cursor.execute("""
                        SELECT * FROM conversations 
                        WHERE project_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (project['id'], limit))
                else:
                    return []
            else:
                cursor.execute("""
                    SELECT * FROM conversations 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            messages = [dict(row) for row in cursor.fetchall()]
            return list(reversed(messages))  # Return in chronological order
    
    def clear_conversation(self, project_name: Optional[str] = None) -> bool:
        """
        Clear conversation history.
        
        Args:
            project_name (Optional[str]): Clear only for specific project.
            
        Returns:
            bool: True if successful.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if project_name:
                project = self.get_project(project_name)
                if project:
                    cursor.execute(
                        "DELETE FROM conversations WHERE project_id = ?",
                        (project['id'],)
                    )
            else:
                cursor.execute("DELETE FROM conversations")
            
            conn.commit()
            return True
    
    # ==================== FILE OPERATION LOGGING ====================
    
    def log_file_operation(
        self,
        operation_type: str,
        file_path: str,
        content: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> int:
        """
        Log a file operation to the database.
        
        Args:
            operation_type (str): Type of operation ('create', 'edit', 'delete').
            file_path (str): Path of the file.
            content (Optional[str]): File content (for create/edit).
            project_name (Optional[str]): Associated project name.
            
        Returns:
            int: ID of the logged operation.
        """
        project_id = None
        if project_name:
            project = self.get_project(project_name)
            if project:
                project_id = project['id']
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO file_operations (project_id, operation_type, file_path, content)
                VALUES (?, ?, ?, ?)
            """, (project_id, operation_type, file_path, content))
            conn.commit()
            return cursor.lastrowid
    
    def get_file_operations(
        self,
        project_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get file operation history.
        
        Args:
            project_name (Optional[str]): Filter by project name.
            limit (int): Maximum number of operations to retrieve.
            
        Returns:
            List[Dict[str, Any]]: List of file operations.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if project_name:
                project = self.get_project(project_name)
                if project:
                    cursor.execute("""
                        SELECT * FROM file_operations 
                        WHERE project_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (project['id'], limit))
                else:
                    return []
            else:
                cursor.execute("""
                    SELECT * FROM file_operations 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== USER PREFERENCES ====================
    
    def set_preference(self, key: str, value: Any) -> bool:
        """
        Set a user preference.
        
        Args:
            key (str): Preference key.
            value (Any): Preference value (will be JSON encoded).
            
        Returns:
            bool: True if successful.
        """
        value_json = json.dumps(value)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_json))
            conn.commit()
            return True
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            key (str): Preference key.
            default (Any): Default value if preference not found.
            
        Returns:
            Any: Preference value or default.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM user_preferences WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return default
    
    def delete_preference(self, key: str) -> bool:
        """
        Delete a user preference.
        
        Args:
            key (str): Preference key to delete.
            
        Returns:
            bool: True if successful.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_preferences WHERE key = ?",
                (key,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """
        Get all user preferences.
        
        Returns:
            Dict[str, Any]: Dictionary of all preferences.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_preferences")
            rows = cursor.fetchall()
            
            return {key: json.loads(value) for key, value in rows}
    
    # ==================== UTILITY METHODS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dict[str, Any]: Statistics about the database contents.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count projects
            cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = cursor.fetchone()[0]
            
            # Count conversations
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conversation_count = cursor.fetchone()[0]
            
            # Count file operations
            cursor.execute("SELECT COUNT(*) FROM file_operations")
            file_op_count = cursor.fetchone()[0]
            
            # Get most recent activity
            cursor.execute("""
                SELECT MAX(timestamp) FROM (
                    SELECT timestamp FROM conversations
                    UNION ALL
                    SELECT timestamp FROM file_operations
                )
            """)
            last_activity = cursor.fetchone()[0]
            
            return {
                "total_projects": project_count,
                "total_messages": conversation_count,
                "total_file_operations": file_op_count,
                "last_activity": last_activity
            }
    
    def backup_database(self, backup_path: Path) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path (Path): Path for the backup file.
            
        Returns:
            bool: True if successful.
        """
        import shutil
        try:
            shutil.copy2(str(self.db_path), str(backup_path))
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """Close any open database connections."""
        # Connections are managed via context manager, so this is mainly for cleanup
        pass


# Create a global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager: The global database manager object.
    """
    return db_manager


if __name__ == "__main__":
    # Test database functionality when executed directly
    print("Testing HyperCLI database...")
    
    db = get_db_manager()
    
    # Test project operations
    print("\n1. Creating test project...")
    try:
        project_id = db.create_project(
            name="test_project",
            description="A test project",
            language="Python"
        )
        print(f"   Created project with ID: {project_id}")
    except sqlite3.IntegrityError:
        print("   Project already exists")
    
    # Test getting projects
    print("\n2. Getting all projects...")
    projects = db.get_all_projects()
    for project in projects:
        print(f"   - {project['name']}: {project['description']}")
    
    # Test conversation operations
    print("\n3. Adding test messages...")
    db.add_message("user", "Hello, how are you?", "test_project")
    db.add_message("assistant", "I'm doing well, thank you!", "test_project")
    
    # Test getting conversation history
    print("\n4. Getting conversation history...")
    history = db.get_conversation_history("test_project")
    for msg in history:
        print(f"   [{msg['role']}] {msg['content'][:50]}...")
    
    # Test statistics
    print("\n5. Database statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\nDatabase test complete!")

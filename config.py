"""
HyperCLI Configuration Module
=============================
This module handles all configuration settings for the HyperCLI application.
It provides centralized configuration management for Ollama server settings,
model parameters, and application-wide constants.

Author: HyperCLI Development Team
Version: 1.0.0
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class Config:
    """
    Centralized configuration manager for HyperCLI.
    
    This class provides a singleton-like interface for accessing and managing
    all configuration options used throughout the HyperCLI application.
    
    Attributes:
        OLLAMA_HOST (str): The hostname or IP address of the Ollama server.
        OLLAMA_PORT (int): The port number for the Ollama server API.
        MODEL_NAME (str): The name of the LLM model to use.
        BASE_DIR (Path): The base directory for the HyperCLI application.
        PROJECTS_DIR (Path): The directory where projects are stored.
        DATABASE_PATH (Path): The path to the SQLite database file.
        SYSTEM_PROMPT_PATH (Path): The path to the system prompt JSON file.
        MAX_TOKENS (int): Maximum number of tokens for model responses.
        TEMPERATURE (float): Temperature setting for model generation.
        TIMEOUT (int): Timeout in seconds for API requests.
    """
    
    # ========================================================================
    # OLLAMA SERVER CONFIGURATION
    # ========================================================================
    # To switch between local and external Ollama servers, modify the 
    # OLLAMA_HOST value below:
    #   - Local server: "localhost" or "127.0.0.1"
    #   - External server: Provide the IP address or hostname of the remote server
    #   - Remote server example: "192.168.1.100" or "ollama.example.com"
    # Note: No notification will be displayed when switching servers.
    # ========================================================================
    
    OLLAMA_HOST: str = "localhost"  # Change to external IP for remote server
    OLLAMA_PORT: int = 11434  # Default Ollama API port
    
    # Model configuration
    MODEL_NAME: str = "deepseek-r1:8b"  # Primary model for code generation
    
    # Alternative models (uncomment to use different models)
    # MODEL_NAME: str = "llama2:7b"
    # MODEL_NAME: str = "codellama:7b"
    # MODEL_NAME: str = "mistral:7b"
    
    # ========================================================================
    # DIRECTORY CONFIGURATION
    # ========================================================================
    
    # Base directory for HyperCLI (automatically detected)
    BASE_DIR: Path = Path(__file__).parent.resolve()
    
    # Projects directory - where all user projects are stored
    PROJECTS_DIR: Path = BASE_DIR / "projects"
    
    # Database file path for storing conversation history and project metadata
    DATABASE_PATH: Path = BASE_DIR / "database.db"
    
    # System prompt JSON file path - contains the AI's "instincts"
    SYSTEM_PROMPT_PATH: Path = BASE_DIR / "system_prompt.json"
    
    # ========================================================================
    # MODEL GENERATION PARAMETERS
    # ========================================================================
    
    # Maximum number of tokens in the response
    MAX_TOKENS: int = 4096
    
    # Temperature for sampling (higher = more creative, lower = more deterministic)
    # Recommended range: 0.1 to 1.0
    TEMPERATURE: float = 0.7
    
    # Top-p sampling parameter (nucleus sampling)
    TOP_P: float = 0.9
    
    # Top-k sampling parameter
    TOP_K: int = 40
    
    # Repetition penalty to reduce repetitive outputs
    REPETITION_PENALTY: float = 1.1
    
    # Stop sequences that will terminate generation
    STOP_SEQUENCES: list = []
    
    # ========================================================================
    # API AND NETWORK SETTINGS
    # ========================================================================
    
    # Timeout for API requests in seconds
    TIMEOUT: int = 300  # Increased timeout (5 min) for large code generation tasks
    
    # Number of retry attempts for failed API calls
    MAX_RETRIES: int = 3
    
    # Delay between retries in seconds
    RETRY_DELAY: float = 2.0
    
    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    
    # Enable streaming responses for live text display
    ENABLE_STREAMING: bool = True
    
    # Enable verbose logging for debugging
    DEBUG_MODE: bool = False
    
    # Maximum conversation history to keep in memory
    MAX_HISTORY_LENGTH: int = 50
    
    # Auto-save interval for conversation history (in messages)
    AUTO_SAVE_INTERVAL: int = 5
    
    # ========================================================================
    # UI/UX SETTINGS
    # ========================================================================
    
    # Color scheme for terminal output
    COLOR_THEME: str = "dark"  # Options: "dark", "light", "monokai"
    
    # Animation speed for typing effects (in seconds per character)
    TYPING_ANIMATION_SPEED: float = 0.02
    
    # Show progress bars for long operations
    SHOW_PROGRESS_BARS: bool = True
    
    # Display file creation animations
    SHOW_FILE_ANIMATIONS: bool = True
    
    # ========================================================================
    # FILE OPERATIONS SETTINGS
    # ========================================================================
    
    # Maximum file size that can be read/edited (in bytes)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    
    # Supported file extensions for editing
    SUPPORTED_EXTENSIONS: tuple = (
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
        ".html", ".css", ".scss", ".less", ".json", ".xml", ".yaml", ".yml",
        ".md", ".txt", ".sql", ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"
    )
    
    # Default encoding for file operations
    DEFAULT_ENCODING: str = "utf-8"
    
    # Backup files before editing (creates .bak files)
    CREATE_BACKUPS: bool = True
    
    # ========================================================================
    # DATABASE SETTINGS
    # ========================================================================
    
    # Database connection timeout in seconds
    DB_TIMEOUT: int = 30
    
    # Enable WAL mode for better concurrent access
    DB_WAL_MODE: bool = True
    
    # ========================================================================
    # SECURITY SETTINGS
    # ========================================================================
    
    # Prevent operations outside the projects directory
    RESTRICT_TO_PROJECTS_DIR: bool = True
    
    # Blocked commands that cannot be executed
    BLOCKED_COMMANDS: tuple = ("rm -rf", "del /s", "format", "mkfs")
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def __init__(self):
        """Initialize configuration and ensure directories exist."""
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        
    def _initialize_defaults(self) -> None:
        """Initialize default values for mutable types."""
        if self.STOP_SEQUENCES is None:
            object.__setattr__(type(self), 'STOP_SEQUENCES', [])
    
    @classmethod
    def get_ollama_url(cls) -> str:
        """
        Get the full URL for the Ollama API endpoint.
        
        Returns:
            str: The complete URL for Ollama API access.
        """
        return f"http://{cls.OLLAMA_HOST}:{cls.OLLAMA_PORT}"
    
    @classmethod
    def get_api_endpoint(cls, path: str) -> str:
        """
        Construct a full API endpoint URL.
        
        Args:
            path (str): The API path (e.g., "/api/generate", "/api/chat")
            
        Returns:
            str: The complete API endpoint URL.
        """
        base_url = cls.get_ollama_url()
        return f"{base_url}{path}"
    
    @classmethod
    def validate_model(cls, model_name: Optional[str] = None) -> bool:
        """
        Validate if the specified model name is properly formatted.
        
        Args:
            model_name (Optional[str]): The model name to validate.
            
        Returns:
            bool: True if valid, False otherwise.
        """
        if model_name is None:
            model_name = cls.MODEL_NAME
        
        # Basic validation: should contain at least one character
        return bool(model_name and len(model_name.strip()) > 0)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Export current configuration as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary containing all configuration values.
        """
        return {
            "ollama_host": cls.OLLAMA_HOST,
            "ollama_port": cls.OLLAMA_PORT,
            "model_name": cls.MODEL_NAME,
            "base_dir": str(cls.BASE_DIR),
            "projects_dir": str(cls.PROJECTS_DIR),
            "database_path": str(cls.DATABASE_PATH),
            "system_prompt_path": str(cls.SYSTEM_PROMPT_PATH),
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "timeout": cls.TIMEOUT,
            "enable_streaming": cls.ENABLE_STREAMING,
            "debug_mode": cls.DEBUG_MODE,
            "color_theme": cls.COLOR_THEME,
        }
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration settings for debugging."""
        print("\n" + "="*60)
        print("HyperCLI Configuration")
        print("="*60)
        for key, value in cls.to_dict().items():
            print(f"{key}: {value}")
        print("="*60 + "\n")


# Create a global configuration instance
config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The global configuration object.
    """
    return config


if __name__ == "__main__":
    # Run configuration validation when executed directly
    print("Validating HyperCLI configuration...")
    cfg = get_config()
    cfg.print_config()
    print("Configuration validation complete.")

#!/usr/bin/env python3
"""
HyperCLI - AI-Powered Terminal Code Assistant
==============================================
Main application module for HyperCLI, a terminal-based AI assistant
specialized in code generation and project management.

This application provides:
- Interactive chat interface with LLM (via Ollama)
- Project creation and management
- File creation, editing, and reading capabilities
- Conversation history and memory
- Live streaming responses

Author: HyperCLI Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import signal
import threading
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
from datetime import datetime
import re

# Import local modules
from config import config, get_config
from database import DatabaseManager, get_db_manager


class Colors:
    """ANSI color codes for terminal output."""
    
    # Basic colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    @classmethod
    def disable(cls):
        """Disable colors for non-supporting terminals."""
        cls.RESET = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.ITALIC = ""
        cls.UNDERLINE = ""
        cls.BLACK = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""
        cls.WHITE = ""
        cls.BRIGHT_RED = ""
        cls.BRIGHT_GREEN = ""
        cls.BRIGHT_YELLOW = ""
        cls.BRIGHT_BLUE = ""
        cls.BRIGHT_MAGENTA = ""
        cls.BRIGHT_CYAN = ""
        cls.BRIGHT_WHITE = ""
        cls.BG_BLACK = ""
        cls.BG_RED = ""
        cls.BG_GREEN = ""
        cls.BG_YELLOW = ""
        cls.BG_BLUE = ""
        cls.BG_MAGENTA = ""
        cls.BG_CYAN = ""
        cls.BG_WHITE = ""


class OllamaClient:
    """
    Client for interacting with Ollama API.
    
    This class handles all communication with the Ollama server,
    including model queries, text generation, and streaming responses.
    """
    
    def __init__(self, host: str = None, port: int = None, model: str = None):
        """
        Initialize the Ollama client.
        
        Args:
            host (str): Ollama server host.
            port (int): Ollama server port.
            model (str): Model name to use.
        """
        self.host = host or config.OLLAMA_HOST
        self.port = port or config.OLLAMA_PORT
        self.model = model or config.MODEL_NAME
        self.base_url = f"http://{self.host}:{self.port}"
        self.session_history: List[Dict[str, str]] = []
    
    def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        stream: bool = False
    ) -> Any:
        """
        Make an HTTP request to the Ollama API.
        
        Args:
            endpoint (str): API endpoint path.
            data (Dict[str, Any]): Request data.
            stream (bool): Whether to stream the response.
            
        Returns:
            Response data or generator for streaming.
        """
        import urllib.request
        import urllib.error
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        req_data = json.dumps(data).encode('utf-8')
        request = urllib.request.Request(
            url,
            data=req_data,
            headers=headers,
            method='POST'
        )
        
        try:
            if stream:
                return self._stream_response(request)
            else:
                with urllib.request.urlopen(
                    request,
                    timeout=config.TIMEOUT
                ) as response:
                    return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {e}")
        except Exception as e:
            raise RuntimeError(f"API request failed: {e}")
    
    def _stream_response(self, request) -> Generator[Dict[str, Any], None, None]:
        """
        Stream response from Ollama API.
        
        Args:
            request: HTTP request object.
            
        Yields:
            Response chunks as dictionaries.
        """
        import urllib.request
        
        with urllib.request.urlopen(
            request,
            timeout=config.TIMEOUT
        ) as response:
            for line in response:
                if line:
                    try:
                        yield json.loads(line.decode('utf-8'))
                    except json.JSONDecodeError:
                        continue
    
    def check_connection(self) -> bool:
        """
        Check if Ollama server is accessible.
        
        Returns:
            bool: True if connection successful.
        """
        try:
            import urllib.request
            url = f"{self.base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.status == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List[str]: List of model names.
        """
        try:
            import urllib.request
            url = f"{self.base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return [model['name'] for model in data.get('models', [])]
        except Exception:
            return []
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = True
    ) -> Generator[str, None, None] | str:
        """
        Generate text from the model.
        
        Args:
            prompt (str): User prompt.
            system_prompt (Optional[str]): System instruction.
            stream (bool): Whether to stream the response.
            
        Returns:
            Generated text or generator for streaming.
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add session history
        messages.extend(self.session_history[-config.MAX_HISTORY_LENGTH:])
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": config.TEMPERATURE,
                "top_p": config.TOP_P,
                "top_k": config.TOP_K,
                "num_predict": config.MAX_TOKENS,
            }
        }
        
        if config.STOP_SEQUENCES:
            data["options"]["stop"] = config.STOP_SEQUENCES
        
        if stream:
            return self._generate_stream(data)
        else:
            result = self._make_request("/api/chat", data, stream=False)
            content = result.get("message", {}).get("content", "")
            
            # Update session history
            self.session_history.append({"role": "user", "content": prompt})
            self.session_history.append({"role": "assistant", "content": content})
            
            # Trim history if too long
            if len(self.session_history) > config.MAX_HISTORY_LENGTH:
                self.session_history = self.session_history[-config.MAX_HISTORY_LENGTH:]
            
            return content
    
    def _generate_stream(self, data: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Generate text with streaming.
        
        Args:
            data (Dict[str, Any]): Request data.
            
        Yields:
            Text chunks as they are generated.
        """
        full_response = ""
        
        for chunk in self._make_request("/api/chat", data, stream=True):
            if "message" in chunk:
                content = chunk["message"].get("content", "")
                if content:
                    full_response += content
                    yield content
            
            # Check if done
            if chunk.get("done", False):
                # Update session history
                user_prompt = data["messages"][-1]["content"]
                self.session_history.append({"role": "user", "content": user_prompt})
                self.session_history.append({"role": "assistant", "content": full_response})
                
                # Trim history if too long
                if len(self.session_history) > config.MAX_HISTORY_LENGTH:
                    self.session_history = self.session_history[-config.MAX_HISTORY_LENGTH:]
                
                break
    
    def clear_history(self) -> None:
        """Clear the session history."""
        self.session_history = []
    
    def set_model(self, model_name: str) -> None:
        """
        Set the model to use.
        
        Args:
            model_name (str): New model name.
        """
        self.model = model_name


class HyperCLI:
    """
    Main HyperCLI application class.
    
    This class orchestrates all functionality including:
    - Command parsing and execution
    - Chat interface
    - File operations
    - Project management
    """
    
    def __init__(self):
        """Initialize the HyperCLI application."""
        self.config = get_config()
        self.db = get_db_manager()
        self.ollama = OllamaClient()
        self.current_project: Optional[Dict[str, Any]] = None
        self.system_prompt: Optional[str] = None
        self.running = True
        self.pending_files: List[Dict[str, str]] = []
        
        # Load system prompt
        self._load_system_prompt()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        print("\n")
        self.print_help()
        self.running = False
    
    def _load_system_prompt(self) -> None:
        """Load system prompt from JSON file."""
        try:
            with open(self.config.SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Extract the actual prompt from the JSON structure
                prompt_data = data.get('system_prompt', {})
                
                # Build a comprehensive system prompt from the JSON
                identity = prompt_data.get('core_identity', {})
                guidelines = prompt_data.get('behavioral_guidelines', {})
                expertise = prompt_data.get('technical_expertise', {})
                special = prompt_data.get('special_instructions', {})
                
                system_prompt = f"""You are {identity.get('role', 'an AI assistant')}.

PERSONALITY TRAITS:
{', '.join(identity.get('personality_traits', []))}

COMMUNICATION STYLE:
- Tone: {identity.get('communication_style', {}).get('tone', 'professional')}
- Clarity: High
- Technical depth: Adaptable to user expertise

CODE QUALITY STANDARDS:
{chr(10).join('- ' + std for std in guidelines.get('code_quality_standards', []))}

INTERACTION PRINCIPLES:
{chr(10).join('- ' + principle for principle in guidelines.get('interaction_principles', []))}

FILE OPERATIONS ETHICS:
{chr(10).join('- ' + ethic for ethic in guidelines.get('file_operations_ethics', []))}

TECHNICAL EXPERTISE:
Expert in: {', '.join(expertise.get('programming_languages', {}).get('expert_level', []))}

SPECIAL INSTRUCTIONS FOR FILE CREATION:
When creating files, you must:
1. Present the complete file structure to the user first
2. Wait for explicit confirmation before creating any files
3. Create files one by one with clear progress indication
4. Verify each file was created successfully
5. Provide a summary of all created files

SPECIAL INSTRUCTIONS FOR FILE EDITING:
When editing files, you must:
1. Read and display the current file content first
2. Propose specific changes with explanations
3. Wait for user approval
4. Apply changes carefully, preserving unrelated code
5. Verify the edited file is syntactically correct

Remember: Always ask for confirmation before creating or modifying files.
Current working directory for projects: {self.config.PROJECTS_DIR}
"""
                self.system_prompt = system_prompt
                
        except FileNotFoundError:
            self.system_prompt = """You are an expert software developer AI assistant.
You specialize in code generation, file creation, and project management.
Always ask for confirmation before creating or modifying files.
Provide clean, well-documented, and efficient code."""
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}Error loading system prompt: {e}{Colors.RESET}")
            self.system_prompt = """You are an expert software developer AI assistant."""
    
    def print_banner(self) -> None:
        """Print the application banner."""
        banner = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════╗
║                                                              ║
║              {Colors.BOLD}{Colors.BRIGHT_WHITE}HyperCLI{Colors.RESET}{Colors.BRIGHT_CYAN} - AI Code Assistant           ║
║                                                              ║
║         Powered by Ollama • {Colors.BRIGHT_YELLOW}{self.config.MODEL_NAME}{Colors.RESET}{Colors.BRIGHT_CYAN}                ║
║                                                              ║
║         Type {Colors.BOLD}{Colors.BRIGHT_GREEN}/help{Colors.RESET}{Colors.BRIGHT_CYAN} for available commands          ║
║                                                              ║
╚══════════════════════════════════════════════════════════╝{Colors.RESET}
"""
        print(banner)
        
        # Check connection
        if not self.ollama.check_connection():
            print(f"{Colors.BRIGHT_YELLOW}⚠ Warning: Cannot connect to Ollama server at {self.ollama.base_url}{Colors.RESET}")
            print(f"{Colors.DIM}Make sure Ollama is running: ollama serve{Colors.RESET}\n")
        else:
            print(f"{Colors.BRIGHT_GREEN}✓ Connected to Ollama server{Colors.RESET}\n")
    
    def print_help(self) -> None:
        """Print help information."""
        help_text = f"""
{Colors.BOLD}{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}
{Colors.BOLD}{Colors.BRIGHT_WHITE}                    HYPERCLI COMMANDS                      {Colors.RESET}
{Colors.BOLD}{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}

  {Colors.BRIGHT_GREEN}/help{Colors.RESET}                    Display this help message
  
  {Colors.BRIGHT_GREEN}/create <project_name>{Colors.RESET}   Create a new project in the projects directory
                              You'll be asked what type of project and files to create
  
  {Colors.BRIGHT_GREEN}/edit <filename> <request>{Colors.RESET}
                              View and edit an existing file based on your request
                              Example: /edit main.py Add error handling
  
  {Colors.BRIGHT_GREEN}/projects{Colors.RESET}                List all available projects
  
  {Colors.BRIGHT_GREEN}/useproject <name>{Colors.RESET}       Switch to a specific project
  
  {Colors.BRIGHT_GREEN}/currentproject{Colors.RESET}          Show the currently active project
  
  {Colors.BRIGHT_GREEN}/exit{Colors.RESET} or {Colors.BRIGHT_GREEN}Ctrl+C{Colors.RESET}     Exit the application

{Colors.BOLD}{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}
{Colors.DIM}Tips:{Colors.RESET}
  • Be specific in your requests for better results
  • Review code suggestions before accepting
  • Use /edit to modify existing files
  • All projects are stored in: {Colors.BRIGHT_YELLOW}{self.config.PROJECTS_DIR}{Colors.RESET}
{Colors.BOLD}{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}
"""
        print(help_text)
    
    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Get the current active project."""
        # First check in-memory
        if self.current_project:
            return self.current_project
        
        # Then check database
        project = self.db.get_active_project()
        if project:
            self.current_project = project
            return project
        
        return None
    
    def ensure_project_selected(self) -> bool:
        """Ensure a project is selected before operations."""
        if not self.get_current_project():
            print(f"\n{Colors.BRIGHT_YELLOW}⚠ No project selected!{Colors.RESET}")
            print(f"Use {Colors.BRIGHT_GREEN}/useproject <name>{Colors.RESET} to select a project")
            print(f"Or {Colors.BRIGHT_GREEN}/create <name>{Colors.RESET} to create a new one\n")
            return False
        return True
    
    def handle_create_project(self, args: str) -> None:
        """
        Handle project creation command.
        
        Args:
            args (str): Project name and optional description.
        """
        if not args.strip():
            print(f"\n{Colors.RED}✗ Please provide a project name{Colors.RESET}")
            print(f"Usage: {Colors.BRIGHT_GREEN}/create <project_name>{Colors.RESET}\n")
            return
        
        # Parse project name and optional description
        parts = args.strip().split(' ', 1)
        project_name = parts[0]
        user_description = parts[1] if len(parts) > 1 else ""
        
        # Validate project name
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', project_name):
            print(f"\n{Colors.RED}✗ Invalid project name{Colors.RESET}")
            print("Project name must start with a letter and contain only letters, numbers, hyphens, and underscores\n")
            return
        
        # Check if project already exists
        existing = self.db.get_project(project_name)
        if existing:
            print(f"\n{Colors.BRIGHT_YELLOW}⚠ Project '{project_name}' already exists{Colors.RESET}")
            print(f"Use {Colors.BRIGHT_GREEN}/useproject {project_name}{Colors.RESET} to switch to it\n")
            return
        
        # Create project directory
        project_path = self.config.PROJECTS_DIR / project_name
        
        try:
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Save to database
            self.db.create_project(
                name=project_name,
                description=f"Created with HyperCLI",
                language=""
            )
            
            print(f"\n{Colors.BRIGHT_GREEN}✓ Project '{project_name}' created successfully{Colors.RESET}")
            print(f"Location: {Colors.DIM}{project_path}{Colors.RESET}\n")
            
            # Get project details from user if not provided
            if not user_description:
                print(f"{Colors.BRIGHT_CYAN}Describe what you want to build:{Colors.RESET}")
                print("Examples: 'A Python Flask REST API with JWT authentication', 'A React todo app with TypeScript', etc.\n")
                
                try:
                    project_type = input(f"{Colors.BRIGHT_WHITE}> Your project description: {Colors.RESET}")
                except (EOFError, KeyboardInterrupt):
                    print("\n")
                    return
            else:
                project_type = user_description
                print(f"{Colors.BRIGHT_CYAN}Project description:{Colors.RESET} {Colors.WHITE}{project_type}{Colors.RESET}\n")
            
            # Generate complete structure and files with AI
            print(f"\n{Colors.DIM}AI is designing your project structure and generating all files...{Colors.RESET}\n")
            
            ai_prompt = f"""The user wants to create a new project called '{project_name}'.
Project description: {project_type}

IMPORTANT: You must generate COMPLETE, READY-TO-RUN code for ALL files.

Your response MUST follow this EXACT format:

## Project Structure
```
project_root/
├── folder1/
│   ├── file1.py
│   └── file2.py
├── folder2/
│   └── file3.js
└── README.md
```

## Files

### filename: path/to/file1.py
```language
# Complete content of file1.py
# Include ALL necessary imports, classes, functions
# Make it production-ready
```

### filename: path/to/file2.js
```language
// Complete content of file2.js
```

### filename: README.md
```markdown
# {project_name}

## Description
{project_type}

## Installation
Step-by-step installation instructions.

## Usage
How to run and use this project.

## Features
- Feature 1
- Feature 2

## License
MIT
```

REQUIREMENTS:
1. Create ALL necessary files for a working project
2. Include complete, runnable code (no placeholders like "add code here")
3. Include proper error handling
4. Add comments explaining complex logic
5. Create a comprehensive README.md
6. Include .gitignore appropriate for the project type
7. Include requirements.txt or package.json if needed
8. Make sure all imports and dependencies are correct

Generate at least 5-10 files for a complete project structure."""
            
            try:
                response = self.ollama.generate(ai_prompt, self.system_prompt, stream=False)
                
                # Display the generated structure
                print(f"\n{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}                    GENERATED PROJECT STRUCTURE                  {Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}\n")
                print(f"{Colors.WHITE}{response}{Colors.RESET}\n")
                
                # Ask for confirmation ONCE before creating files
                confirm = input(f"{Colors.BRIGHT_GREEN}Create all these files automatically? (yes/no): {Colors.RESET}").strip().lower()
                
                if confirm in ['yes', 'y']:
                    # Parse and create ALL files at once
                    self._parse_and_create_all_files(project_name, response, project_type)
                    
                    # Auto-select the project
                    self.db.set_active_project(project_name)
                    self.current_project = self.db.get_project(project_name)
                    print(f"\n{Colors.BRIGHT_GREEN}✓ Project setup complete! Switched to: {project_name}{Colors.RESET}\n")
                    print(f"{Colors.DIM}Tip: Use /edit <filename> <request> to modify any file{Colors.RESET}\n")
                else:
                    print(f"\n{Colors.DIM}Files not created. You can use /edit later to add files manually.{Colors.RESET}\n")
                    
            except Exception as e:
                print(f"\n{Colors.RED}✗ Error generating project: {e}{Colors.RESET}\n")
                
        except Exception as e:
            print(f"\n{Colors.RED}✗ Failed to create project: {e}{Colors.RESET}\n")
    
    def _parse_and_create_all_files(
        self,
        project_name: str,
        ai_response: str,
        project_type: str
    ) -> None:
        """
        Parse AI response and create ALL files automatically with live animation.
        
        Args:
            project_name (str): Name of the project.
            ai_response (str): AI's complete file structure and content.
            project_type (str): Type of project.
        """
        project_path = self.config.PROJECTS_DIR / project_name
        
        # Advanced parsing for the new format: ### filename: path/to/file.ext
        files_to_create = []
        lines = ai_response.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        language_marker = ""
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for "### filename: path/to/file.ext" pattern
            filename_match = re.match(r'^###\s*filename:\s*(.+)$', line.strip())
            if filename_match:
                current_file = filename_match.group(1).strip()
                i += 1
                continue
            
            # Check for code block markers
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    # Extract language if present
                    lang_part = line.strip()[3:].strip()
                    language_marker = lang_part if lang_part else ""
                    
                    # If we don't have a filename yet, try to infer from context
                    if not current_file:
                        # Try to guess from language
                        if language_marker in ['python', 'py']:
                            current_file = f"main.py"
                        elif language_marker in ['javascript', 'js']:
                            current_file = f"index.js"
                        elif language_marker in ['typescript', 'ts']:
                            current_file = f"index.ts"
                        elif language_marker in ['html']:
                            current_file = f"index.html"
                        elif language_marker in ['css']:
                            current_file = f"style.css"
                        elif language_marker in ['json']:
                            current_file = f"config.json"
                        elif language_marker in ['markdown', 'md']:
                            current_file = f"README.md"
                        elif language_marker in ['txt']:
                            current_file = f"file.txt"
                        elif language_marker in ['gitignore']:
                            current_file = f".gitignore"
                        elif language_marker in ['yaml', 'yml']:
                            current_file = f"config.yaml"
                        elif language_marker in ['toml']:
                            current_file = f"pyproject.toml"
                        elif language_marker in ['sh', 'bash']:
                            current_file = f"script.sh"
                        elif language_marker in ['sql']:
                            current_file = f"schema.sql"
                        else:
                            current_file = f"file.{language_marker}" if language_marker else "file.txt"
                    
                    current_content = []
                else:
                    # Ending a code block
                    in_code_block = False
                    if current_file and current_content:
                        files_to_create.append({
                            'path': current_file,
                            'content': '\n'.join(current_content)
                        })
                        print(f"  {Colors.BRIGHT_GREEN}✓{Colors.RESET} Parsed: {Colors.BRIGHT_WHITE}{current_file}{Colors.RESET}")
                    current_file = None
                    current_content = []
                    language_marker = ""
            elif in_code_block:
                current_content.append(line)
            
            i += 1
        
        # If no files were parsed, create basic structure
        if not files_to_create:
            print(f"{Colors.DIM}Creating essential project files...{Colors.RESET}\n")
            
            # Create README.md
            readme_content = f"""# {project_name}

{project_type}

## Getting Started

This project was created with HyperCLI - AI Code Assistant.

## Installation

```bash
# Add installation steps here
```

## Usage

```bash
# Add usage examples here
```

## Features

- Feature 1
- Feature 2

## Project Structure

```
{project_name}/
├── README.md
├── .gitignore
└── src/
    └── main.py
```

## License

MIT License

## Generated by

HyperCLI - AI-Powered Terminal Code Assistant
"""
            files_to_create.append({'path': 'README.md', 'content': readme_content})
            
            # Create .gitignore
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
env/
venv/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Node.js (if applicable)
node_modules/
npm-debug.log
yarn-error.log
"""
            files_to_create.append({'path': '.gitignore', 'content': gitignore_content})
            
            # Create a basic main.py for Python projects
            if 'python' in project_type.lower() or 'flask' in project_type.lower() or 'django' in project_type.lower():
                main_py_content = f'''#!/usr/bin/env python3
"""
{project_name} - {project_type}

Generated by HyperCLI - AI Code Assistant
"""

def main():
    """Main entry point."""
    print("Welcome to {project_name}!")
    print("Start building your amazing project here.")


if __name__ == "__main__":
    main()
'''
                files_to_create.append({'path': 'main.py', 'content': main_py_content})
            
            # Create requirements.txt for Python projects
            if 'python' in project_type.lower():
                req_content = """# Core dependencies
# Add your project dependencies here
# Example:
# flask==2.3.0
# requests==2.31.0
"""
                files_to_create.append({'path': 'requirements.txt', 'content': req_content})
        
        # Display summary of files to create
        print(f"\n{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}                    FILES TO CREATE ({len(files_to_create)} total)                   {Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}\n")
        
        for i, file_info in enumerate(files_to_create, 1):
            status_icon = f"{Colors.BRIGHT_GREEN}✓{Colors.RESET}"
            print(f"  [{i}/{len(files_to_create)}] {status_icon} {Colors.BRIGHT_WHITE}{file_info['path']}{Colors.RESET} ({len(file_info['content'])} chars)")
        
        print()
        
        # Create each file with live typing animation
        created_count = 0
        failed_count = 0
        
        for i, file_info in enumerate(files_to_create, 1):
            file_path = file_info['path']
            content = file_info['content']
            
            # Handle subdirectories
            full_path = project_path / file_path
            
            # Create parent directories if needed
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"  [{i}/{len(files_to_create)}] {Colors.RED}✗{Colors.RESET} Failed to create directory for {Colors.BRIGHT_WHITE}{file_path}{Colors.RESET}: {e}")
                failed_count += 1
                continue
            
            # Animate file creation with live typing effect
            print(f"  [{i}/{len(files_to_create)}] Creating {Colors.BRIGHT_WHITE}{file_path}{Colors.RESET}...", end=" ", flush=True)
            
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    # Live typing animation for smaller files
                    if config.SHOW_FILE_ANIMATIONS and len(content) < 3000:
                        animation_speed = config.TYPING_ANIMATION_SPEED * 0.3
                        for char_idx, char in enumerate(content):
                            f.write(char)
                            # Flush every few characters for performance
                            if char_idx % 10 == 0:
                                f.flush()
                            time.sleep(animation_speed)
                        f.flush()
                    else:
                        # Write directly for large files
                        f.write(content)
                
                print(f"{Colors.BRIGHT_GREEN}✓ Done{Colors.RESET} ({len(content)} bytes)")
                created_count += 1
                
                # Log operation to database
                self.db.log_file_operation(
                    operation_type='create',
                    file_path=file_path,
                    content=content,
                    project_name=project_name
                )
                
            except Exception as e:
                print(f"{Colors.RED}✗ Error: {str(e)[:50]}{Colors.RESET}")
                failed_count += 1
        
        # Final summary
        print(f"\n{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}                    CREATION SUMMARY                           {Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}═══════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"\n  {Colors.BRIGHT_GREEN}✓ Successfully created:{Colors.RESET} {created_count} files")
        if failed_count > 0:
            print(f"  {Colors.BRIGHT_RED}✗ Failed to create:{Colors.RESET} {failed_count} files")
        
        print(f"\n  {Colors.DIM}Project location: {Colors.BRIGHT_WHITE}{project_path}{Colors.RESET}")
        print(f"  {Colors.DIM}Tip: Use '{Colors.BRIGHT_GREEN}/edit <filename> <request>{Colors.RESET}' to modify any file{Colors.RESET}")
        print()
    
    def handle_edit_file(self, args: str) -> None:
        """
        Handle file editing command.
        
        Args:
            args (str): Filename and edit request.
        """
        if not self.ensure_project_selected():
            return
        
        parts = args.strip().split(None, 1)
        if len(parts) < 2:
            print(f"\n{Colors.RED}✗ Please provide filename and edit request{Colors.RESET}")
            print(f"Usage: {Colors.BRIGHT_GREEN}/edit <filename> <request>{Colors.RESET}")
            print(f"Example: /edit main.py Add error handling\n")
            return
        
        filename = parts[0]
        request = parts[1]
        
        project = self.get_current_project()
        project_path = Path(project['path'])
        file_path = project_path / filename
        
        # Check if file exists
        if not file_path.exists():
            print(f"\n{Colors.RED}✗ File not found: {filename}{Colors.RESET}")
            print(f"Available files in project:\n")
            self._list_project_files(project['name'])
            return
        
        # Read current content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except Exception as e:
            print(f"\n{Colors.RED}✗ Error reading file: {e}{Colors.RESET}\n")
            return
        
        # Display current content
        print(f"\n{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Current content of {Colors.BRIGHT_WHITE}{filename}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.DIM}{current_content}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}\n")
        
        # Ask AI for edits
        print(f"{Colors.DIM}Analyzing and applying requested changes...{Colors.RESET}\n")
        
        ai_prompt = f"""Current file: {filename}
Current content:
```
{current_content}
```

User request: {request}

Please provide:
1. Analysis of what needs to be changed
2. The complete updated file content

Format your response with:
- ANALYSIS: section explaining the changes
- UPDATED CODE: section with the complete new file content in a code block"""
        
        try:
            response = self.ollama.generate(ai_prompt, self.system_prompt, stream=False)
            
            print(f"{Colors.BRIGHT_CYAN}Proposed Changes:{Colors.RESET}")
            print(f"{Colors.WHITE}{response}{Colors.RESET}\n")
            
            # Extract the updated code from response
            updated_content = self._extract_code_block(response)
            
            if not updated_content:
                updated_content = response
            
            # Ask for confirmation
            confirm = input(f"{Colors.BRIGHT_GREEN}Apply these changes? (yes/no): {Colors.RESET}").strip().lower()
            
            if confirm in ['yes', 'y']:
                # Create backup
                if config.CREATE_BACKUPS:
                    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(current_content)
                    print(f"{Colors.DIM}Backup created: {backup_path.name}{Colors.RESET}\n")
                
                # Write updated content with animation
                print(f"Updating {Colors.BRIGHT_WHITE}{filename}{Colors.RESET}...", end=" ")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    if config.SHOW_FILE_ANIMATIONS and len(updated_content) < 5000:
                        for char in updated_content:
                            f.write(char)
                            f.flush()
                            time.sleep(config.TYPING_ANIMATION_SPEED * 0.5)
                    else:
                        f.write(updated_content)
                
                print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET}")
                
                # Log operation
                self.db.log_file_operation(
                    operation_type='edit',
                    file_path=filename,
                    content=updated_content,
                    project_name=project['name']
                )
                
                print(f"\n{Colors.BRIGHT_GREEN}✓ File updated successfully{Colors.RESET}\n")
            else:
                print(f"\n{Colors.DIM}Changes not applied.{Colors.RESET}\n")
                
        except Exception as e:
            print(f"\n{Colors.RED}✗ Error: {e}{Colors.RESET}\n")
    
    def _extract_code_block(self, text: str) -> str:
        """
        Extract code block from text.
        
        Args:
            text (str): Text containing code block.
            
        Returns:
            str: Extracted code or empty string.
        """
        # Look for markdown code blocks
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[-1].strip()
        
        return ""
    
    def _list_project_files(self, project_name: str) -> None:
        """
        List all files in a project.
        
        Args:
            project_name (str): Name of the project.
        """
        project = self.db.get_project(project_name)
        if not project:
            print(f"{Colors.RED}Project not found{Colors.RESET}")
            return
        
        project_path = Path(project['path'])
        
        if not project_path.exists():
            print(f"{Colors.RED}Project directory not found{Colors.RESET}")
            return
        
        print(f"\n{Colors.BRIGHT_CYAN}Files in {project_name}:{Colors.RESET}")
        
        for root, dirs, files in os.walk(project_path):
            level = root.replace(str(project_path), '').count(os.sep)
            indent = '  ' * level
            
            rel_root = os.path.relpath(root, project_path)
            if rel_root != '.':
                print(f"{indent}{Colors.BRIGHT_BLUE}📁 {os.path.basename(root)}/{Colors.RESET}")
            
            sub_indent = '  ' * (level + 1)
            for file in files:
                ext = Path(file).suffix
                color = Colors.WHITE
                
                if ext in ['.py']:
                    color = Colors.BRIGHT_YELLOW
                elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                    color = Colors.BRIGHT_YELLOW
                elif ext in ['.html', '.css']:
                    color = Colors.BRIGHT_BLUE
                elif ext in ['.md', '.txt']:
                    color = Colors.DIM
                elif ext in ['.json', '.yaml', '.yml']:
                    color = Colors.BRIGHT_MAGENTA
                
                print(f"{sub_indent}{color}📄 {file}{Colors.RESET}")
        
        print()
    
    def handle_list_projects(self) -> None:
        """List all projects."""
        projects = self.db.get_all_projects()
        
        if not projects:
            print(f"\n{Colors.DIM}No projects found.{Colors.RESET}")
            print(f"Create one with: {Colors.BRIGHT_GREEN}/create <project_name>{Colors.RESET}\n")
            return
        
        print(f"\n{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Available Projects{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}\n")
        
        current = self.get_current_project()
        current_name = current['name'] if current else None
        
        for project in projects:
            is_current = project['name'] == current_name
            marker = f"{Colors.BRIGHT_GREEN}●{Colors.RESET}" if is_current else " "
            status = f"{Colors.DIM}(active){Colors.RESET}" if is_current else ""
            
            print(f"  {marker} {Colors.BRIGHT_WHITE}{project['name']}{Colors.RESET} {status}")
            
            if project.get('description'):
                print(f"      {Colors.DIM}{project['description']}{Colors.RESET}")
            
            print(f"      {Colors.DIM}Path: {project['path']}{Colors.RESET}")
            print(f"      {Colors.DIM}Created: {project['created_at']}{Colors.RESET}")
            print()
        
        print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}\n")
    
    def handle_use_project(self, args: str) -> None:
        """
        Switch to a different project.
        
        Args:
            args (str): Project name.
        """
        if not args.strip():
            print(f"\n{Colors.RED}✗ Please provide a project name{Colors.RESET}")
            print(f"Usage: {Colors.BRIGHT_GREEN}/useproject <name>{Colors.RESET}\n")
            return
        
        project_name = args.strip()
        project = self.db.get_project(project_name)
        
        if not project:
            print(f"\n{Colors.RED}✗ Project not found: {project_name}{Colors.RESET}")
            print(f"Use {Colors.BRIGHT_GREEN}/projects{Colors.RESET} to see available projects\n")
            return
        
        # Check if directory exists
        if not Path(project['path']).exists():
            print(f"\n{Colors.RED}✗ Project directory not found: {project['path']}{Colors.RESET}\n")
            return
        
        # Set as active
        self.db.set_active_project(project_name)
        self.current_project = project
        
        # Clear conversation history for new project
        self.ollama.clear_history()
        
        print(f"\n{Colors.BRIGHT_GREEN}✓ Switched to project: {project_name}{Colors.RESET}")
        print(f"Location: {Colors.DIM}{project['path']}{Colors.RESET}\n")
        
        # Show project files
        self._list_project_files(project_name)
    
    def handle_current_project(self) -> None:
        """Display current project information."""
        project = self.get_current_project()
        
        if not project:
            print(f"\n{Colors.DIM}No project currently selected.{Colors.RESET}")
            print(f"Use {Colors.BRIGHT_GREEN}/useproject <name>{Colors.RESET} to select one\n")
            return
        
        print(f"\n{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Current Project{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}\n")
        
        print(f"  {Colors.BRIGHT_WHITE}Name:{Colors.RESET} {project['name']}")
        print(f"  {Colors.BRIGHT_WHITE}Description:{Colors.RESET} {project.get('description', 'N/A')}")
        print(f"  {Colors.BRIGHT_WHITE}Path:{Colors.RESET} {project['path']}")
        print(f"  {Colors.BRIGHT_WHITE}Language:{Colors.RESET} {project.get('language', 'N/A')}")
        print(f"  {Colors.BRIGHT_WHITE}Created:{Colors.RESET} {project['created_at']}")
        print(f"  {Colors.BRIGHT_WHITE}Updated:{Colors.RESET} {project['updated_at']}")
        
        print(f"\n{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}\n")
    
    def chat_with_ai(self, user_input: str) -> None:
        """
        Send user input to AI and display response.
        
        Args:
            user_input (str): User's message.
        """
        # Get current project context
        project = self.get_current_project()
        project_context = ""
        
        if project:
            project_context = f"\n\nCurrent project: {project['name']}\nProject path: {project['path']}"
        
        # Prepare prompt
        full_prompt = user_input + project_context
        
        # Save user message to database
        if project:
            self.db.add_message(
                role='user',
                content=user_input,
                project_name=project['name']
            )
        
        # Generate response with streaming
        print(f"\n{Colors.BRIGHT_CYAN}Thinking...{Colors.RESET}\n")
        
        try:
            response_generator = self.ollama.generate(
                full_prompt,
                self.system_prompt,
                stream=True
            )
            
            print(f"{Colors.BRIGHT_WHITE}", end="")
            
            full_response = ""
            for chunk in response_generator:
                print(chunk, end="", flush=True)
                full_response += chunk
            
            print(f"{Colors.RESET}\n")
            
            # Save assistant response to database
            if project:
                self.db.add_message(
                    role='assistant',
                    content=full_response,
                    project_name=project['name']
                )
                
        except Exception as e:
            print(f"\n{Colors.RED}✗ Error: {e}{Colors.RESET}\n")
    
    def run(self) -> None:
        """Main application loop."""
        self.print_banner()
        
        # Load last active project
        project = self.db.get_active_project()
        if project and Path(project['path']).exists():
            self.current_project = project
            print(f"{Colors.DIM}Loaded project: {project['name']}{Colors.RESET}\n")
        
        while self.running:
            try:
                # Get project indicator
                project = self.get_current_project()
                if project:
                    prompt = f"{Colors.BRIGHT_GREEN}[{project['name']}]{Colors.RESET} {Colors.BRIGHT_WHITE}> {Colors.RESET}"
                else:
                    prompt = f"{Colors.DIM}> {Colors.RESET}"
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                else:
                    # Regular chat
                    if not self.ensure_project_selected():
                        continue
                    self.chat_with_ai(user_input)
                    
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n")
                continue
        
        print(f"\n{Colors.BRIGHT_CYAN}Goodbye! 👋{Colors.RESET}\n")
    
    def handle_command(self, command: str) -> None:
        """
        Parse and execute commands.
        
        Args:
            command (str): Full command string.
        """
        parts = command.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self.print_help()
        
        elif cmd == '/create':
            self.handle_create_project(args)
        
        elif cmd == '/edit':
            self.handle_edit_file(args)
        
        elif cmd == '/projects':
            self.handle_list_projects()
        
        elif cmd == '/useproject':
            self.handle_use_project(args)
        
        elif cmd == '/currentproject':
            self.handle_current_project()
        
        elif cmd == '/exit':
            self.running = False
        
        else:
            print(f"\n{Colors.RED}✗ Unknown command: {cmd}{Colors.RESET}")
            print(f"Type {Colors.BRIGHT_GREEN}/help{Colors.RESET} for available commands\n")


def main():
    """Application entry point."""
    print(f"{Colors.DIM}Initializing HyperCLI...{Colors.RESET}\n")
    
    app = HyperCLI()
    app.run()


if __name__ == "__main__":
    main()

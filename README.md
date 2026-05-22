# HyperCLI - Complete User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Quick Start](#quick-start)
6. [Commands Reference](#commands-reference)
7. [Features](#features)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Introduction

**HyperCLI** is a powerful terminal-based AI code assistant that leverages local LLM models (via Ollama) to help you create, edit, and manage software projects directly from your command line.

### Key Features

- 🤖 **AI-Powered Code Generation**: Create entire project structures with AI assistance
- 📁 **Project Management**: Organize and switch between multiple projects effortlessly
- ✏️ **File Editing**: View and edit files with AI-suggested improvements
- 💾 **Persistent Memory**: Conversation history stored in SQLite database
- 🎨 **Live Streaming**: Watch AI responses appear in real-time
- 🔒 **Local & Private**: Runs entirely on your machine with no data sent to external servers
- 🎯 **Code Specialist**: Optimized for software development tasks

---

## Prerequisites

Before installing HyperCLI, ensure you have the following:

### Required Software

1. **Python 3.8 or higher**
   ```bash
   python --version  # Should show Python 3.8+
   ```

2. **Ollama** (https://ollama.ai)
   - Download and install from https://ollama.ai
   - Or install via command line:
     ```bash
     # Linux/Mac
     curl -fsSL https://ollama.ai/install.sh | sh
     
     # Windows
     # Download installer from https://ollama.ai/download
     ```

3. **Required Model**
   ```bash
   ollama pull deepseek-r1:8b
   ```

### Optional (Recommended)

- Git for version control
- A code editor for reviewing generated files

---

## Installation

### Step 1: Clone or Download HyperCLI

```bash
# Navigate to your desired location
cd ~/projects  # or any directory you prefer

# If using git
git clone <repository-url> hypercli
cd hypercli

# Or simply extract the downloaded files
```

### Step 2: Verify Directory Structure

Ensure you have these files:
```
hypercli/
├── config.py           # Configuration settings
├── main.py             # Main application
├── database.py         # Database management
├── system_prompt.json  # AI personality & instructions
├── requirements.txt    # Dependencies (minimal)
├── run.bat            # Windows launcher
└── projects/          # Your projects folder
```

### Step 3: Install Dependencies (Optional)

HyperCLI uses only Python standard library, so no installation needed:
```bash
# Optional: If you want enhanced features
pip install -r requirements.txt
```

### Step 4: Start Ollama Server

```bash
# In a separate terminal, start Ollama
ollama serve
```

Keep this terminal running while using HyperCLI.

---

## Configuration

### Basic Configuration (config.py)

Open `config.py` to customize settings:

#### Changing Ollama Server

```python
# For local server (default)
OLLAMA_HOST: str = "localhost"
OLLAMA_PORT: int = 11434

# For remote/external server
OLLAMA_HOST: str = "192.168.1.100"  # IP of remote server
OLLAMA_PORT: int = 11434
```

⚠️ **Note**: Server changes are manual only - no notifications displayed.

#### Changing the Model

```python
# Default model
MODEL_NAME: str = "deepseek-r1:8b"

# Alternative models
# MODEL_NAME: str = "llama2:7b"
# MODEL_NAME: str = "codellama:7b"
# MODEL_NAME: str = "mistral:7b"
```

#### Adjusting AI Behavior

```python
# Temperature (0.1 = focused, 1.0 = creative)
TEMPERATURE: float = 0.7

# Maximum response length
MAX_TOKENS: int = 4096

# Enable/disable animations
SHOW_FILE_ANIMATIONS: bool = True
TYPING_ANIMATION_SPEED: float = 0.02
```

### System Prompt (system_prompt.json)

This file defines the AI's personality and capabilities. Advanced users can modify it to:
- Change coding style preferences
- Add domain-specific knowledge
- Customize interaction patterns

⚠️ **Warning**: Modifying system_prompt.json requires understanding of JSON structure.

---

## Quick Start

### Starting HyperCLI

#### Windows
```cmd
run.bat
```

#### Linux/Mac
```bash
python main.py
```

### First Steps

1. **Start the application**
   ```
   $ python main.py
   
   ╔══════════════════════════════════════════════════════════╗
   ║                                                              ║
   ║              HyperCLI - AI Code Assistant                    ║
   ║                                                              ║
   ║         Powered by Ollama • deepseek-r1:8b                  ║
   ║                                                              ║
   ║         Type /help for available commands                   ║
   ║                                                              ║
   ╚══════════════════════════════════════════════════════════╝
   
   ✓ Connected to Ollama server
   ```

2. **Create your first project**
   ```
   > /create my_website
   ```

3. **Describe your project**
   ```
   What type of project would you like to create?
   Examples: Python web app, JavaScript CLI tool, React component library, etc.
   
   > Project type/description: A simple Flask web application
   ```

4. **Review AI suggestions**
   - AI will propose a project structure
   - Review the suggested files and folders
   - Confirm with "yes" to create files

5. **Start chatting**
   ```
   [my_website] > How do I add a new route?
   ```

---

## Commands Reference

### `/help`
Display all available commands with descriptions.

**Example:**
```
> /help
```

---

### `/create <project_name>`
Create a new project in the `projects/` directory.

**Parameters:**
- `project_name`: Name for your project (letters, numbers, hyphens, underscores)

**Workflow:**
1. Enter project name
2. Describe project type
3. Review AI-suggested structure
4. Confirm file creation
5. Automatically switch to new project

**Examples:**
```
> /create todo_app
> /create api_server
> /create data_pipeline
```

---

### `/edit <filename> <request>`
View and edit an existing file based on your request.

**Parameters:**
- `filename`: Name of file to edit (must exist in current project)
- `request`: Description of changes needed

**Workflow:**
1. Current file content is displayed
2. AI analyzes and proposes changes
3. Review proposed changes
4. Confirm to apply edits
5. Backup created automatically (if enabled)

**Examples:**
```
> /edit main.py Add error handling to the database connection
> /edit app.js Convert this to use async/await
> /edit utils.py Add type hints to all functions
> /edit styles.css Make the buttons blue with rounded corners
```

---

### `/projects`
List all available projects with details.

**Shows:**
- Project name
- Active status (● for current)
- Description
- Path location
- Creation date

**Example:**
```
> /projects

============================================================
Available Projects
============================================================

  ● todo_app (active)
      A task management application
      Path: /workspace/projects/todo_app
      Created: 2024-01-15 10:30:00

  api_server
      REST API backend
      Path: /workspace/projects/api_server
      Created: 2024-01-14 09:15:00

============================================================
```

---

### `/useproject <name>`
Switch to a different project.

**Parameters:**
- `name`: Name of project to switch to

**Effects:**
- Changes active project
- Clears conversation history
- Shows project files

**Examples:**
```
> /useproject todo_app
> /useproject api_server
```

---

### `/currentproject`
Display information about the currently active project.

**Shows:**
- Project name
- Description
- Full path
- Programming language
- Creation/update dates

**Example:**
```
> /currentproject

============================================================
Current Project
============================================================

  Name: todo_app
  Description: A task management application
  Path: /workspace/projects/todo_app
  Language: Python
  Created: 2024-01-15 10:30:00
  Updated: 2024-01-15 14:22:00

============================================================
```

---

### `/exit` or `Ctrl+C`
Exit the application gracefully.

**Examples:**
```
> /exit
```
Or press `Ctrl+C`

---

## Features

### 1. Project Management

#### Creating Projects
- AI-suggested project structures
- Automatic directory creation
- Database tracking
- Initial file generation

#### Switching Projects
- Instant context switching
- Isolated conversation history
- File tree visualization

### 2. File Operations

#### File Creation
- Multiple files simultaneously
- Subdirectory support
- Live writing animation
- Operation logging

#### File Editing
- Full content preview
- AI-powered modifications
- Automatic backups (.bak files)
- Syntax preservation

#### Supported File Types
- **Python**: `.py`
- **JavaScript/TypeScript**: `.js`, `.ts`, `.jsx`, `.tsx`
- **Web**: `.html`, `.css`, `.scss`
- **Data**: `.json`, `.xml`, `.yaml`, `.yml`
- **Documentation**: `.md`, `.txt`
- **Shell**: `.sh`, `.bash`, `.zsh`, `.ps1`, `.bat`
- And many more...

### 3. AI Capabilities

#### Code Generation
- Complete project scaffolding
- Function implementation
- Class design
- API endpoints
- Database models
- Test cases

#### Code Editing
- Refactoring suggestions
- Bug fixes
- Performance optimization
- Adding features
- Style improvements
- Documentation

#### Best Practices
- Clean code principles
- Design patterns
- Security considerations
- Error handling
- Type safety
- Testing strategies

### 4. Memory & Persistence

#### Conversation History
- Stored in SQLite database
- Project-specific contexts
- Configurable retention limit
- Automatic cleanup

#### File Operation Logs
- Track all changes
- Audit trail
- Rollback capability

#### User Preferences
- Persistent settings
- Custom configurations
- Workflow optimizations

### 5. UI/UX Features

#### Visual Feedback
- Color-coded output
- Progress indicators
- File creation animations
- Status messages

#### Terminal Enhancements
- ANSI color support
- Clear formatting
- Readable layouts
- Intuitive prompts

---

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to Ollama server"

**Symptoms:**
```
⚠ Warning: Cannot connect to Ollama server at http://localhost:11434
```

**Solutions:**
```bash
# Check if Ollama is running
ollama serve

# Verify port
curl http://localhost:11434/api/tags

# Restart Ollama
# Windows: Restart Ollama application
# Linux/Mac: pkill ollama && ollama serve
```

---

#### 2. "Model not found"

**Symptoms:**
```
Error: model 'deepseek-r1:8b' not found
```

**Solution:**
```bash
ollama pull deepseek-r1:8b
```

---

#### 3. "Permission denied" errors

**Symptoms:**
```
✗ Failed to create project: [Errno 13] Permission denied
```

**Solutions:**
- Run as administrator (Windows)
- Use sudo (Linux/Mac) - not recommended
- Fix directory permissions:
  ```bash
  chmod -R 755 /path/to/hypercli
  ```

---

#### 4. Database errors

**Symptoms:**
```
sqlite3.Error: database is locked
```

**Solutions:**
- Close other instances of HyperCLI
- Delete database.db (will reset history)
- Check file permissions

---

#### 5. Slow response times

**Causes:**
- Large code files
- Complex requests
- Limited hardware resources

**Solutions:**
- Reduce MAX_TOKENS in config.py
- Use smaller model (e.g., deepseek-r1:1b)
- Break requests into smaller chunks
- Close other applications

---

#### 6. Colors not displaying correctly

**Symptoms:**
- Garbled characters in terminal
- No colors shown

**Solutions:**
```python
# In config.py, disable colors
# Or in main.py, call Colors.disable()
```

**Windows:**
- Use Windows Terminal instead of cmd
- Enable ANSI support in registry

---

## Best Practices

### 1. Project Organization

✅ **Do:**
- Use descriptive project names
- Keep projects in the `projects/` directory
- Regularly backup important projects
- Use version control (Git)

❌ **Don't:**
- Use spaces in project names
- Create too many nested directories
- Store sensitive data in projects

### 2. Effective Prompts

✅ **Good Examples:**
```
"Create a Flask REST API with user authentication"
"Add input validation to the login function"
"Refactor this class to use dependency injection"
"Write unit tests for the payment module"
```

❌ **Vague Examples:**
```
"Make it better"
"Fix everything"
"Add stuff"
```

### 3. File Editing

✅ **Best Practices:**
- Review proposed changes carefully
- Test code after editing
- Keep backups enabled
- Edit one concern at a time

❌ **Avoid:**
- Editing multiple unrelated sections
- Skipping review step
- Disabling backups

### 4. Performance

✅ **Optimize:**
- Keep conversation history manageable
- Use appropriate model size
- Close unused projects
- Regular database maintenance

### 5. Security

✅ **Important:**
- Review AI-generated code before production use
- Don't commit sensitive data
- Validate all user inputs
- Follow security best practices

---

## Advanced Usage

### Customizing System Prompt

Edit `system_prompt.json` to:
- Add domain-specific knowledge
- Change coding conventions
- Modify interaction style

### Multiple Ollama Servers

Configure different servers for different needs:
```python
# config.py
# Development server
OLLAMA_HOST = "localhost"

# Production server (for testing)
# OLLAMA_HOST = "production-server.local"
```

### Database Management

```python
from database import get_db_manager

db = get_db_manager()

# Get statistics
stats = db.get_statistics()

# Backup database
db.backup_database(Path("backup.db"))

# Clear conversation
db.clear_conversation("project_name")
```

---

## Support & Community

### Resources
- Documentation: This guide
- GitHub: https://github.com/dashbehrad/HyperCLI.git
- Issues: https://github.com/dashbehrad/HyperCLI.git/issues

### Contributing
Contributions welcome! Please:
1. Fork the repository at https://github.com/dashbehrad/HyperCLI.git
2. Create feature branch
3. Submit pull request

---

## License

MIT License - See LICENSE file for details

---

## Version History

### v1.0.0
- Initial release
- Core functionality
- Project management with automatic file creation
- File operations with live animation
- AI integration with Ollama (deepseek-r1:8b)
- Database persistence
- Enhanced system prompt for generating comprehensive code files
- No confirmation prompts - files created automatically

---

**Happy Coding with HyperCLI! 🚀**

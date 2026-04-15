"""
JARVIS Coding Agent

Handles code generation, file operations, editing, debugging, and execution.
Can create, edit, debug and deploy full-stack applications.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import subprocess
import json
import re
from jarvis.core.logging import get_logger
from jarvis.core.engine import Command

logger = get_logger(__name__)


class CodingAgent:
    """Agent for coding tasks and operations."""

    def __init__(self, workspace: Optional[Path] = None):
        """
        Initialize the coding agent.
        
        Args:
            workspace: Root directory for code operations (default: current directory)
        """
        self.workspace = workspace or Path.cwd()
        logger.info(f"CodingAgent initialized with workspace: {self.workspace}")

    async def execute(self, command: Command) -> Dict[str, Any]:
        """
        Execute a coding command.
        
        Args:
            command: Parsed command
            
        Returns:
            Execution result
        """
        logger.log_action("coding_task_started", {
            "action": command.action,
            "parameters": command.parameters
        })

        try:
            if command.action == "create":
                return await self.create_project(command)
            elif command.action == "write":
                return await self.write_code(command)
            elif command.action == "build":
                return await self.build_project(command)
            elif command.action == "debug":
                return await self.debug_code(command)
            else:
                return {
                    "success": False,
                    "error": f"Unknown coding action: {command.action}"
                }
        except Exception as e:
            logger.log_error("coding_execution", str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def create_project(self, command: Command) -> Dict[str, Any]:
        """Create a new coding project."""
        logger.debug("Creating project...")
        
        try:
            # Extract project name from parameters
            words = command.parameters.get("raw_words", [])
            project_name = words[-1] if len(words) > 0 else "project"
            
            # Detect project type from keywords
            text_lower = command.raw_text.lower()
            project_type = "generic"
            if "api" in text_lower or "fastapi" in text_lower:
                project_type = "fastapi_api"
            elif "website" in text_lower or "react" in text_lower:
                project_type = "react_app"
            elif "cli" in text_lower:
                project_type = "cli_app"
            
            project_dir = self.workspace / project_name
            
            # Create project structure
            if project_type == "fastapi_api":
                await self._create_fastapi_project(project_dir, project_name)
            elif project_type == "react_app":
                await self._create_react_project(project_dir, project_name)
            else:
                project_dir.mkdir(parents=True, exist_ok=True)
                (project_dir / "README.md").write_text(f"# {project_name}\n\nProject created by JARVIS AI Agent\n")
            
            logger.log_action("project_created", {
                "project_name": project_name,
                "project_type": project_type,
                "location": str(project_dir)
            })
            
            return {
                "success": True,
                "output": f"Project '{project_name}' created successfully",
                "details": {
                    "project_type": project_type,
                    "location": str(project_dir),
                    "project_name": project_name
                }
            }
        except Exception as e:
            logger.log_error("project_creation", str(e))
            return {
                "success": False,
                "error": f"Failed to create project: {str(e)}"
            }
    
    async def _create_fastapi_project(self, project_dir: Path, name: str):
        """Create a FastAPI project structure."""
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main.py
        main_py = """from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI(title="%s")

@app.get("/")
async def root():
    return {"message": "Welcome to %s"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""" % (name, name)
        (project_dir / "main.py").write_text(main_py)
        
        # Create requirements.txt
        requirements = """fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
"""
        (project_dir / "requirements.txt").write_text(requirements)
        
        # Create README
        readme = f"""# {name}

FastAPI project created by JARVIS AI Agent.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Visit http://localhost:8000/docs for API documentation.
"""
        (project_dir / "README.md").write_text(readme)
    
    async def _create_react_project(self, project_dir: Path, name: str):
        """Create a React project structure."""
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package.json
        package_json = {
            "name": name,
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            }
        }
        (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # Create public and src directories
        (project_dir / "public").mkdir(exist_ok=True)
        (project_dir / "src").mkdir(exist_ok=True)
        
        # Create index.js
        index_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
"""
        (project_dir / "src" / "index.js").write_text(index_js)
        
        # Create App.js
        app_js = """import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Welcome to %s</h1>
      <p>Created by JARVIS AI Agent</p>
    </div>
  );
}

export default App;
""" % name
        (project_dir / "src" / "App.js").write_text(app_js)
        
        # Create README
        readme = f"""# {name}

React project created by JARVIS AI Agent.

## Setup

```bash
npm install
```

## Run

```bash
npm start
```
"""
        (project_dir / "README.md").write_text(readme)

    async def write_code(self, command: Command) -> Dict[str, Any]:
        """Write code based on specification."""
        logger.debug("Writing code...")
        
        try:
            words = command.parameters.get("raw_words", [])
            
            # Extract file name and content
            file_name = "generated_code.py" if len(words) < 2 else words[-1]
            if not file_name.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java')):
                file_name += ".py"
            
            # Generate basic code structure
            code_content = self._generate_code_template(file_name, command.raw_text)
            
            file_path = self.workspace / file_name
            file_path.write_text(code_content)
            
            logger.log_action("code_written", {
                "file": str(file_path),
                "lines": len(code_content.split('\n'))
            })
            
            return {
                "success": True,
                "output": f"Code written to {file_name}",
                "details": {
                    "files_created": 1,
                    "file_path": str(file_path),
                    "lines_of_code": len(code_content.split('\n'))
                }
            }
        except Exception as e:
            logger.log_error("code_writing", str(e))
            return {
                "success": False,
                "error": f"Failed to write code: {str(e)}"
            }
    
    def _generate_code_template(self, filename: str, description: str) -> str:
        """Generate code template based on file type and description."""
        if filename.endswith('.py'):
            return f'''"""
{description}

Auto-generated by JARVIS AI Agent
"""

def main():
    """Main entry point."""
    print("Hello from {filename}")

if __name__ == "__main__":
    main()
'''
        elif filename.endswith(('.js', '.ts')):
            return f'''/**
 * {description}
 * Auto-generated by JARVIS AI Agent
 */

function main() {{
    console.log("Hello from {filename}");
}}

main();
'''
        else:
            return f'''// {description}
// Auto-generated by JARVIS AI Agent

fn main() {{
    println!("Hello from {filename}");
}}
'''

    async def build_project(self, command: Command) -> Dict[str, Any]:
        """Build a project."""
        logger.debug("Building project...")
        
        try:
            # Detect build system
            build_cmd = None
            
            if (self.workspace / "Makefile").exists():
                build_cmd = "make"
            elif (self.workspace / "package.json").exists():
                build_cmd = "npm run build"
            elif (self.workspace / "setup.py").exists():
                build_cmd = "python setup.py build"
            elif (self.workspace / "Cargo.toml").exists():
                build_cmd = "cargo build"
            elif (self.workspace / "go.mod").exists():
                build_cmd = "go build"
            else:
                return {
                    "success": False,
                    "error": "No build system detected in workspace"
                }
            
            logger.log_action("build_started", {"command": build_cmd})
            
            result = await asyncio.to_thread(
                self.execute_command,
                build_cmd
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "output": "Build completed successfully",
                    "details": {
                        "build_system": build_cmd.split()[0],
                        "stdout": result.get("stdout", "")[:500]
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Build failed: {result.get('stderr', 'Unknown error')[:500]}"
                }
        except Exception as e:
            logger.log_error("build_failed", str(e))
            return {
                "success": False,
                "error": f"Build error: {str(e)}"
            }

    async def debug_code(self, command: Command) -> Dict[str, Any]:
        """Debug code and find issues."""
        logger.debug("Analyzing code for issues...")
        
        try:
            issues = []
            
            # Scan Python files
            py_files = list(self.workspace.glob("**/*.py"))
            for file in py_files[:10]:  # Limit to first 10 files
                try:
                    content = file.read_text()
                    
                    # Check for common issues
                    if "except:" in content:
                        issues.append(f"{file.name}: Bare except clause found")
                    if "eval(" in content:
                        issues.append(f"{file.name}: eval() usage detected (security risk)")
                    if "__pycache__" in content:
                        issues.append(f"{file.name}: Reference to __pycache__ in code")
                    if "print(" in content and "logger" not in content.lower():
                        issues.append(f"{file.name}: Using print() instead of logger")
                    
                    # Count lines
                    lines = len(content.split('\n'))
                    if lines > 500:
                        issues.append(f"{file.name}: Large file ({lines} lines)")
                
                except Exception as e:
                    logger.debug(f"Error reading {file}: {e}")
            
            # Scan for common patterns
            all_files = list(self.workspace.glob("**/*"))
            text_files = [f for f in all_files if f.is_file() and f.suffix in {'.py', '.js', '.ts', '.go'}]
            
            logger.log_action("debug_analysis_complete", {
                "files_scanned": len(text_files),
                "issues_found": len(issues)
            })
            
            return {
                "success": True,
                "output": f"Found {len(issues)} potential issues",
                "details": {
                    "issues_found": len(issues),
                    "issues": issues[:10],  # Top 10 issues
                    "files_scanned": len(text_files)
                }
            }
        except Exception as e:
            logger.log_error("debug_analysis_failed", str(e))
            return {
                "success": False,
                "error": f"Debug analysis failed: {str(e)}"
            }

    async def execute_command(self, cmd: str, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        Execute a shell command safely.
        
        Args:
            cmd: Command to execute
            cwd: Working directory
            
        Returns:
            Command output and result
        """
        cwd = cwd or self.workspace
        
        logger.log_action("execute_shell_command", {
            "command": cmd,
            "working_dir": str(cwd)
        })
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            logger.log_error("command_execution", "Command timeout")
            return {
                "success": False,
                "error": "Command timeout"
            }
        except Exception as e:
            logger.log_error("command_execution", str(e))
            return {
                "success": False,
                "error": str(e)
            }

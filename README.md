# RhinoMCP

RhinoMCP connects Rhino3D to Claude AI via the Model Context Protocol (MCP), enabling Claude to directly interact with and control Rhino3D for AI-assisted 3D modeling, analysis, and design workflows.

## Project Overview

This integration consists of two main components:

1. **Rhino Plugin**: A socket server that runs inside Rhino's Python editor, providing a communication interface to Rhino's functionality.
2. **MCP Server**: An implementation of the Model Context Protocol that connects Claude AI to the Rhino plugin, enabling AI-controlled operations.

## Features

- Socket-based bidirectional communication between Python and Rhino
- Model Context Protocol server for Claude AI integration
- Support for NURBS curve creation (initial test feature)
- Python script execution within Rhino's context
- Compatible with both Claude Desktop and Windsurf as clients

## Installation

### Requirements

- Rhinoceros 3D (Version 7 or 8)
- Python 3.10 or higher
- Windows 10 or 11

### Install Using uv (Recommended)

```bash
# Create and activate a virtual environment 
mkdir -p .venv
uv venv .venv
source .venv/Scripts/activate  # On Windows with Git Bash

# Install the package
uv pip install -e .
```

### Install Using pip

```bash
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows

# Install the package
pip install -e .
```

## Usage

### Step 1: Start the Rhino Bridge Server

1. Open Rhino
2. Type `EditPythonScript` in the command line to open Rhino's Python editor
3. Open the Rhino server script from `src/rhino_plugin/rhino_server.py`
4. Run the script (F5 or click the Run button)
5. Verify you see "Rhino Bridge started!" in the output panel

### Step 2: Start the MCP Server

```bash
# Activate your virtual environment
source .venv/Scripts/activate  # On Windows with Git Bash

# Start the MCP server
rhinomcp
```

Or run with custom settings:

```bash
rhinomcp --host 127.0.0.1 --port 5000 --rhino-host 127.0.0.1 --rhino-port 8888 --debug
```

### Step 3: Connect with Claude Desktop or Windsurf

Configure Claude Desktop or Windsurf to connect to the MCP server at:

```
ws://127.0.0.1:5000
```

### Example: Creating a NURBS Curve

When connected to Claude, you can ask it to create a NURBS curve in Rhino with a prompt like:

```
Create a NURBS curve in Rhino using points at (0,0,0), (5,10,0), (10,0,0), and (15,10,0).
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/FernandoMaytorena/RhinoMCP.git
cd RhinoMCP

# Create and activate virtual environment
uv venv .venv
source .venv/Scripts/activate  # On Windows with Git Bash

# Install development dependencies
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Style

This project uses Ruff for linting and formatting:

```bash
ruff check .
ruff format .
```

## Project Structure

```
RhinoMCP/
├── src/
│   ├── rhino_plugin/  # Code that runs inside Rhino
│   │   └── rhino_server.py
│   └── rhino_mcp/     # MCP server implementation
│       ├── rhino_client.py
│       └── mcp_server.py
├── tests/             # Test modules
├── docs/              # Documentation
├── config/            # Configuration files
├── ai/                # AI documentation and prompts
├── setup.py           # Package installation
├── requirements.txt   # Package dependencies
└── README.md          # Project documentation
```

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

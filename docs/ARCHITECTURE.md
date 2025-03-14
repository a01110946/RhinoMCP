# RhinoMCP Architecture

This document outlines the architecture and component interactions of the RhinoMCP system, which connects Rhino3D to Claude AI via the Model Context Protocol.

## System Overview

RhinoMCP consists of three main components that work together to enable AI-assisted 3D modeling:

1. **Rhino Plugin**: A socket server running inside Rhino's Python environment
2. **Rhino Client**: A Python client that communicates with the Rhino plugin
3. **MCP Server**: A WebSocket server implementing the Model Context Protocol

These components interact in the following way:

```
Claude AI (Desktop/Windsurf) <--> MCP Server <--> Rhino Client <--> Rhino Plugin <--> Rhino3D
```

## Component Architecture

### 1. Rhino Plugin (`src/rhino_plugin/`)

The Rhino Plugin is a socket server that runs inside Rhino's Python editor environment. It serves as the interface to Rhino's functionality.

#### Key Files:
- `rhino_server.py`: Socket server implementation that listens for commands and executes them in Rhino

#### Responsibilities:
- Accept socket connections from external Python processes
- Receive commands in JSON format
- Execute commands in Rhino's context
- Return results or errors in JSON format
- Manage error handling and recovery

### 2. Rhino Client (`src/rhino_mcp/rhino_client.py`)

The Rhino Client is a Python module that communicates with the Rhino Plugin via a socket connection.

#### Responsibilities:
- Establish and maintain socket connection with the Rhino Plugin
- Format commands as JSON messages
- Send commands to the Rhino Plugin
- Receive and parse responses
- Provide a clean API for the MCP Server

### 3. MCP Server (`src/rhino_mcp/mcp_server.py`)

The MCP Server implements the Model Context Protocol and exposes Rhino functionality as MCP tools.

#### Responsibilities:
- Implement WebSocket server for MCP communication
- Register available Rhino tools
- Validate tool parameters
- Forward tool invocations to the Rhino Client
- Format responses according to MCP specifications

## Data Flow

1. **MCP Request Flow**:
   - Claude AI sends a tool invocation request to the MCP Server
   - MCP Server validates the request and parameters
   - MCP Server formats the request for the Rhino Client
   - Rhino Client sends the request to the Rhino Plugin
   - Rhino Plugin executes the requested operation in Rhino
   - Results flow back through the same path

2. **Communication Formats**:
   - MCP Server <-> Claude AI: JSON-RPC over WebSockets
   - Rhino Client <-> Rhino Plugin: Custom JSON protocol over TCP sockets

## Error Handling

The system implements multiple levels of error handling:

1. **MCP Server**: Validates requests and parameters before forwarding
2. **Rhino Client**: Handles connection issues and timeouts
3. **Rhino Plugin**: Catches exceptions during command execution in Rhino
4. **All Components**: Provide detailed error messages with stack traces for debugging

## Extensibility

The architecture is designed for extensibility:

1. **Tool Registration**: New tools can be added to the MCP Server without modifying the core code
2. **Command Handlers**: The Rhino Plugin can be extended with new command handlers
3. **Protocol Versioning**: Both socket protocols include version information for compatibility

## Security Considerations

1. **Local Connections Only**: Both socket servers bind to localhost by default
2. **No Authentication**: The current implementation assumes a trusted local environment
3. **Input Validation**: All component interfaces validate input to prevent injection attacks

## Future Considerations

1. **Geometry Transfer**: Optimize large geometry data transfer between components
2. **Connection Recovery**: Improve automatic reconnection for better resilience
3. **Tool Expansion**: Add more Rhino operations as MCP tools
4. **Authentication**: Add authentication for non-local deployments

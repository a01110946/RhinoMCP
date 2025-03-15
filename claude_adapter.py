#!/usr/bin/env python
"""
RhinoMCP Claude Desktop Adapter - Bridges between Claude Desktop and Rhino

This adapter provides the stdio interface that Claude Desktop expects,
while communicating with a Rhino socket server.
"""
import sys
import json
import traceback
import asyncio
from rhino_mcp.rhino_client import RhinoClient

# MCP protocol version
PROTOCOL_VERSION = "2024-11-05"

# Global state
rhino_client = None

async def main():
    # Initialize MCP session
    await send_response(0, {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {"name": "rhinomcp", "version": "0.1.0"},
        "capabilities": {
            "tools": {}
        }
    })

    # Connect to Rhino
    global rhino_client
    rhino_client = RhinoClient()
    
    try:
        # Try to connect to Rhino
        if not rhino_client.connect():
            await send_log("error", "Failed to connect to Rhino server. Is it running?")
            return
        
        # Successfully connected
        await send_log("info", f"Connected to Rhino server at {rhino_client.host}:{rhino_client.port}")
        
        # Process incoming messages
        while True:
            # Read a line from stdin
            line = await read_line()
            if not line:
                break
                
            # Parse the message
            try:
                message = json.loads(line)
                
                # Handle the message
                await handle_message(message)
            except json.JSONDecodeError:
                await send_log("error", f"Invalid JSON: {line}")
            except Exception as e:
                await send_log("error", f"Error handling message: {str(e)}")
                traceback.print_exc(file=sys.stderr)
    finally:
        # Disconnect from Rhino
        if rhino_client and rhino_client.connected:
            rhino_client.disconnect()

async def read_line():
    """Read a line from stdin asynchronously"""
    return await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

async def send_message(message):
    """Send a message to stdout"""
    print(json.dumps(message), flush=True)

async def send_response(id, result):
    """Send a JSON-RPC response"""
    await send_message({
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    })

async def send_error(id, code, message, data=None):
    """Send a JSON-RPC error response"""
    error = {
        "code": code,
        "message": message
    }
    if data:
        error["data"] = data
        
    await send_message({
        "jsonrpc": "2.0",
        "id": id,
        "error": error
    })

async def send_log(level, message):
    """Send a log message notification"""
    await send_message({
        "jsonrpc": "2.0",
        "method": "logging/message",
        "params": {
            "level": level,
            "data": message
        }
    })

async def handle_message(message):
    """Handle an incoming JSON-RPC message"""
    if "method" not in message:
        await send_log("error", "Invalid message: no method")
        return
        
    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id")
    
    if method == "initialize":
        # Already sent in main()
        pass
    elif method == "initialized":
        # Client is initialized, nothing to do
        await send_log("info", "Client initialized")
    elif method == "tools/list":
        # Return list of available tools
        await send_response(msg_id, {
            "tools": [{
                "name": "rhino_create_curve",
                "description": "Create a NURBS curve in Rhino",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "points": {
                            "type": "array",
                            "description": "Array of 3D points for the curve",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "number"},
                                    "y": {"type": "number"},
                                    "z": {"type": "number"}
                                },
                                "required": ["x", "y", "z"]
                            },
                            "minItems": 2
                        }
                    },
                    "required": ["points"]
                }
            }]
        })
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        if tool_name == "rhino_create_curve":
            # Call the Rhino client to create a curve
            try:
                points = tool_args.get("points", [])
                if not points or len(points) < 2:
                    await send_error(msg_id, -32602, "At least 2 points are required for a curve")
                    return
                
                # Create the curve
                result = rhino_client.create_curve(points)
                
                if result.get("status") == "success":
                    await send_response(msg_id, {
                        "content": [{
                            "type": "text",
                            "text": f"Curve created successfully: {result.get('message', '')}"
                        }]
                    })
                else:
                    await send_response(msg_id, {
                        "isError": True,
                        "content": [{
                            "type": "text",
                            "text": f"Failed to create curve: {result.get('message', 'Unknown error')}"
                        }]
                    })
            except Exception as e:
                await send_error(msg_id, -32603, f"Internal error: {str(e)}")
        else:
            await send_error(msg_id, -32601, f"Method not found: {tool_name}")
    elif method == "exit":
        # Client wants to exit
        await send_log("info", "Shutting down")
        sys.exit(0)
    else:
        await send_error(msg_id, -32601, f"Method not found: {method}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
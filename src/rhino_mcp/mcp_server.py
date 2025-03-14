"""
MCP Server - Model Context Protocol server for RhinoMCP.

This module implements the Model Context Protocol server that connects
Claude AI to the Rhino client, enabling AI-assisted 3D modeling.

Version: 1.0 (2025-03-13)
"""
from typing import Dict, Any, Optional, List, Union, Callable, TypedDict
import os
import sys
import json
import logging
import argparse
from dataclasses import dataclass, field
import traceback
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol

from rhino_mcp.rhino_client import RhinoClient, Point3d


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("rhino_mcp")


class MCPRequestSchema(TypedDict):
    """Type definition for MCP request schema."""
    jsonrpc: str
    id: Union[str, int]
    method: str
    params: Dict[str, Any]


class MCPResponseSchema(TypedDict):
    """Type definition for MCP response schema."""
    jsonrpc: str
    id: Union[str, int]
    result: Dict[str, Any]


class MCPErrorSchema(TypedDict):
    """Type definition for MCP error response schema."""
    jsonrpc: str
    id: Union[str, int]
    error: Dict[str, Any]


@dataclass
class MCPTool:
    """Class representing an MCP tool.
    
    Attributes:
        name: The name of the tool
        description: The description of the tool
        parameters: The parameters schema of the tool
        handler: The function to handle tool invocation
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class RhinoMCPServer:
    """Model Context Protocol server for RhinoMCP.
    
    This class implements the MCP server that handles communication with
    Claude AI and forwards commands to the Rhino client.
    
    Attributes:
        host: The hostname to bind the server to
        port: The port to bind the server to
        rhino_client: The Rhino client to use for communication with Rhino
        tools: The list of available MCP tools
    """
    
    def __init__(
        self, 
        host: str = '127.0.0.1', 
        port: int = 5000,
        rhino_host: str = '127.0.0.1',
        rhino_port: int = 8888
    ):
        """Initialize the MCP server.
        
        Args:
            host: The hostname to bind the server to
            port: The port to bind the server to
            rhino_host: The hostname of the Rhino Bridge server
            rhino_port: The port of the Rhino Bridge server
        """
        self.host = host
        self.port = port
        self.rhino_client = RhinoClient(rhino_host, rhino_port)
        self.tools: List[MCPTool] = []
        
        # Register built-in tools
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register built-in MCP tools.
        
        This method registers the built-in MCP tools that will be exposed to
        Claude AI through the Model Context Protocol.
        
        Returns:
            None
        """
        # Create NURBS curve tool
        self.tools.append(MCPTool(
            name="rhino_create_curve",
            description="Create a NURBS curve in Rhino",
            parameters={
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
            },
            handler=self._handle_create_curve
        ))
        
        # Tool for pinging Rhino
        self.tools.append(MCPTool(
            name="rhino_ping",
            description="Ping Rhino to check if it's connected and get information",
            parameters={
                "type": "object",
                "properties": {}
            },
            handler=self._handle_ping
        ))
        
        # Tool for running Python script in Rhino
        self.tools.append(MCPTool(
            name="rhino_run_script",
            description="Run a Python script in Rhino's Python context",
            parameters={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Python script to run in Rhino"
                    }
                },
                "required": ["script"]
            },
            handler=self._handle_run_script
        ))
    
    def _handle_create_curve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_curve tool invocation.
        
        Args:
            params: The parameters for the tool invocation
            
        Returns:
            The tool invocation result
            
        Raises:
            ValueError: If the parameters are invalid
        """
        points_data = params.get('points', [])
        
        # Validate points
        if not points_data or len(points_data) < 2:
            raise ValueError("At least 2 points are required to create a curve")
        
        # Format points for Rhino client
        points: List[Point3d] = []
        for pt in points_data:
            points.append({
                'x': float(pt.get('x', 0.0)),
                'y': float(pt.get('y', 0.0)),
                'z': float(pt.get('z', 0.0))
            })
        
        # Ensure Rhino client is connected
        if not self.rhino_client.connected:
            self.rhino_client.connect()
        
        # Create the curve
        result = self.rhino_client.create_curve(points)
        
        # Format response
        if result.get('status') == 'success':
            return {
                'success': True,
                'message': result.get('message', 'Curve created successfully'),
                'data': result.get('data', {})
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to create curve'),
                'error': result.get('traceback', '')
            }
    
    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping tool invocation.
        
        Args:
            params: The parameters for the tool invocation
            
        Returns:
            The tool invocation result
        """
        # Ensure Rhino client is connected
        if not self.rhino_client.connected:
            self.rhino_client.connect()
        
        # Ping Rhino
        result = self.rhino_client.ping()
        
        # Format response
        if result.get('status') == 'success':
            return {
                'success': True,
                'message': result.get('message', 'Rhino is connected'),
                'data': result.get('data', {})
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to ping Rhino'),
                'error': result.get('traceback', '')
            }
    
    def _handle_run_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run_script tool invocation.
        
        Args:
            params: The parameters for the tool invocation
            
        Returns:
            The tool invocation result
            
        Raises:
            ValueError: If the script is empty
        """
        script = params.get('script', '')
        
        # Validate script
        if not script:
            raise ValueError("Script cannot be empty")
        
        # Ensure Rhino client is connected
        if not self.rhino_client.connected:
            self.rhino_client.connect()
        
        # Run the script
        result = self.rhino_client.run_script(script)
        
        # Format response
        if result.get('status') == 'success':
            return {
                'success': True,
                'message': result.get('message', 'Script executed successfully'),
                'data': result.get('data', {})
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to execute script'),
                'error': result.get('traceback', '')
            }
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get the schema for all registered tools.
        
        Returns:
            List of tool schemas in MCP format
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
    
    async def handle_jsonrpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC request.
        
        Args:
            request: The JSON-RPC request
            
        Returns:
            The JSON-RPC response
        """
        # Extract request data
        method = request.get('method', '')
        params = request.get('params', {})
        req_id = request.get('id', 0)
        
        # Handle different methods
        if method == 'rpc.discover':
            # Return MCP server information and tools
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': {
                    'name': 'rhino_mcp',
                    'version': '1.0.0',
                    'functions': self.get_tools_schema()
                }
            }
        elif method.startswith('rhino_'):
            # Handle tool invocation
            for tool in self.tools:
                if tool.name == method:
                    try:
                        result = tool.handler(params)
                        return {
                            'jsonrpc': '2.0',
                            'id': req_id,
                            'result': result
                        }
                    except Exception as e:
                        logger.error(f"Tool error: {str(e)}")
                        traceback.print_exc()
                        return {
                            'jsonrpc': '2.0',
                            'id': req_id,
                            'error': {
                                'code': -32000,
                                'message': str(e),
                                'data': {
                                    'traceback': traceback.format_exc()
                                }
                            }
                        }
        
        # Method not found
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'error': {
                'code': -32601,
                'message': f'Method not found: {method}'
            }
        }
    
    async def handle_websocket(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            None
        """
        logger.info(f"Client connected: {websocket.remote_address}")
        
        # Ensure Rhino client is connected
        if not self.rhino_client.connected:
            try:
                self.rhino_client.connect()
            except Exception as e:
                logger.error(f"Failed to connect to Rhino: {str(e)}")
                await websocket.close(1011, "Failed to connect to Rhino")
                return
        
        try:
            async for message in websocket:
                # Parse the message
                try:
                    request = json.loads(message)
                    logger.info(f"Received request: {request.get('method', 'unknown')}")
                    
                    # Handle the request
                    response = await self.handle_jsonrpc(request)
                    
                    # Send the response
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON")
                    await websocket.send(json.dumps({
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': 'Parse error'
                        }
                    }))
                except Exception as e:
                    logger.error(f"Websocket error: {str(e)}")
                    traceback.print_exc()
                    await websocket.send(json.dumps({
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32603,
                            'message': str(e)
                        }
                    }))
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
        finally:
            logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def start(self) -> None:
        """Start the MCP server.
        
        Returns:
            None
        """
        # Start the WebSocket server
        async with websockets.serve(self.handle_websocket, self.host, self.port):
            logger.info(f"MCP server started at ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    def start_in_thread(self) -> None:
        """Start the MCP server in a separate thread.
        
        Returns:
            None
        """
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            traceback.print_exc()
        finally:
            if self.rhino_client.connected:
                self.rhino_client.disconnect()


def main() -> None:
    """Start the MCP server from the command line.
    
    Returns:
        None
    """
    parser = argparse.ArgumentParser(description='Start the RhinoMCP server')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Hostname to bind the MCP server to')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to bind the MCP server to')
    parser.add_argument('--rhino-host', type=str, default='127.0.0.1',
                        help='Hostname of the Rhino Bridge server')
    parser.add_argument('--rhino-port', type=int, default=8888,
                        help='Port of the Rhino Bridge server')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Start the server
    server = RhinoMCPServer(
        host=args.host,
        port=args.port,
        rhino_host=args.rhino_host,
        rhino_port=args.rhino_port
    )
    
    print(f"Starting RhinoMCP server at ws://{args.host}:{args.port}")
    print(f"Connecting to Rhino at {args.rhino_host}:{args.rhino_port}")
    print("Press Ctrl+C to stop")
    
    try:
        server.start_in_thread()
    except KeyboardInterrupt:
        print("Server stopped by user")


if __name__ == "__main__":
    main()

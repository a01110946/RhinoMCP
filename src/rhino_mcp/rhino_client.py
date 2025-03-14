"""
Rhino Client - Client for communicating with Rhino via socket connection.

This module implements a client that connects to the Rhino Bridge socket server
and provides methods to send commands and receive responses.

Version: 1.0 (2025-03-13)
"""
from typing import Dict, Any, Optional, List, Tuple, Union, TypedDict
import socket
import json
import time
import threading
from dataclasses import dataclass


class Point3d(TypedDict):
    """Type definition for a 3D point with x, y, z coordinates."""
    x: float
    y: float
    z: float


class RhinoClient:
    """Client for communicating with Rhino via socket connection.
    
    This class provides methods to connect to the Rhino Bridge socket server,
    send commands, and receive responses.
    
    Attributes:
        host: The hostname or IP address of the Rhino Bridge server
        port: The port number of the Rhino Bridge server
        socket: The socket connection to the Rhino Bridge server
        connected: Whether the client is currently connected to the server
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        """Initialize the Rhino client.
        
        Args:
            host: The hostname or IP address of the Rhino Bridge server
            port: The port number of the Rhino Bridge server
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to the Rhino Bridge server.
        
        Returns:
            True if connected successfully, False otherwise
            
        Raises:
            ConnectionError: If failed to connect to the server
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to Rhino Bridge at {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            self.connected = False
            raise ConnectionError(
                f"Failed to connect to Rhino Bridge at {self.host}:{self.port}. "
                "Make sure Rhino is running and the Bridge server is started."
            )
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"Connection error: {str(e)}")
    
    def disconnect(self) -> None:
        """Disconnect from the Rhino Bridge server.
        
        Returns:
            None
        """
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
        print("Disconnected from Rhino Bridge")
    
    def send_command(self, cmd_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to the Rhino Bridge server.
        
        Args:
            cmd_type: The type of command to send
            data: The data to send with the command
            
        Returns:
            The response from the server as a dictionary
            
        Raises:
            ConnectionError: If not connected to the server
            RuntimeError: If failed to send command or receive response
        """
        if not self.connected or not self.socket:
            raise ConnectionError("Not connected to Rhino Bridge")
        
        if data is None:
            data = {}
        
        try:
            # Prepare the command
            command = {
                'type': cmd_type,
                'data': data
            }
            
            # Send the command
            self.socket.sendall(json.dumps(command).encode('utf-8'))
            
            # Receive the response
            response_data = self.socket.recv(4096)
            if not response_data:
                raise RuntimeError("No response from server")
            
            # Parse the response
            response = json.loads(response_data.decode('utf-8'))
            return response
        except Exception as e:
            raise RuntimeError(f"Command error: {str(e)}")
    
    def ping(self) -> Dict[str, Any]:
        """Ping the Rhino Bridge server to check connection.
        
        Returns:
            Server information including version and status
            
        Raises:
            ConnectionError: If not connected to the server
        """
        return self.send_command('ping')
    
    def create_curve(self, points: List[Point3d]) -> Dict[str, Any]:
        """Create a NURBS curve in Rhino.
        
        Args:
            points: List of points (each a dict with x, y, z keys)
            
        Returns:
            Response from the server including curve ID if successful
            
        Raises:
            ValueError: If points list is invalid
            ConnectionError: If not connected to the server
        """
        if not points or len(points) < 2:
            raise ValueError("At least 2 points are required to create a curve")
            
        return self.send_command('create_curve', {'points': points})
    
    def refresh_view(self) -> Dict[str, Any]:
        """Refresh the Rhino viewport.
        
        Returns:
            Response from the server
            
        Raises:
            ConnectionError: If not connected to the server
        """
        return self.send_command('refresh_view')
    
    def run_script(self, script: str) -> Dict[str, Any]:
        """Run a Python script in Rhino's Python context.
        
        Args:
            script: The Python script to run
            
        Returns:
            Response from the server including script result
            
        Raises:
            ValueError: If script is empty
            ConnectionError: If not connected to the server
        """
        if not script:
            raise ValueError("Script cannot be empty")
            
        return self.send_command('run_script', {'script': script})


def test_connection(host: str = '127.0.0.1', port: int = 8888) -> bool:
    """Test the connection to the Rhino Bridge server.
    
    Args:
        host: The hostname or IP address of the Rhino Bridge server
        port: The port number of the Rhino Bridge server
        
    Returns:
        True if connected successfully, False otherwise
    """
    client = RhinoClient(host, port)
    try:
        client.connect()
        response = client.ping()
        print(f"Connection successful! Server info:")
        for key, value in response.get('data', {}).items():
            print(f"  {key}: {value}")
        return True
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False
    finally:
        client.disconnect()


if __name__ == "__main__":
    # Simple test when run directly
    test_connection()

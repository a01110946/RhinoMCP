# Python-Rhino Bridge: Setup & Usage Guide

This guide explains how to establish a bidirectional connection between external Python scripts and Rhinoceros 3D, allowing you to control Rhino programmatically from Python running outside the Rhino environment.

## Overview

The Python-Rhino Bridge consists of two main components:

1. **Server Script** - Runs inside Rhino's Python editor and listens for commands
2. **Client Script** - Runs in your external Python environment and sends commands to Rhino

This connection enables:
- Creating Rhino geometry from external Python
- Running custom Python code within Rhino's environment
- Querying information from Rhino
- Building interactive tools that communicate with Rhino

## Requirements

### Software Requirements

- **Rhinoceros 3D**: Version 7 or 8
- **Python**: Version 3.9 or 3.10 (matching your Rhino installation)
- **Operating System**: Windows 10 or 11

### Directory Structure

Create a project folder with the following structure:
```
rhino_windsurf/
  ├── rhino_bridge.py         # Server script (runs in Rhino)
  ├── rhino_client_deluxe.py  # Client script (runs in external Python)
  └── PythonBridgeCommand.py  # Optional Rhino command script
```

## Setup Instructions

### 1. Setting Up the Rhino Server

1. **Create the server script**:
   - Open Rhino
   - Type `EditPythonScript` in the command line to open Rhino's Python editor
   - Create a new script named `rhino_bridge.py`
   - Copy the server script code (provided below) into this file
   - Save the file to your project directory

2. **Running the server**:
   - With the `rhino_bridge.py` file open in Rhino's Python editor
   - Click the "Run" button or press F5
   - Verify you see "Rhino Bridge started!" in the output panel
   - Keep this script running as long as you need the connection

### 2. Setting Up the Python Client

1. **Python environment setup**:
   - Create a virtual environment (recommended): 
     ```
     python -m venv .venv_rhino
     .venv_rhino\Scripts\activate  # On Windows
     ```
   - This isolates your project dependencies from other Python projects

2. **Create the client script**:
   - Create a new file named `rhino_client_deluxe.py` in your project directory
   - Copy the client script code (provided below) into this file

3. **Running the client**:
   - Ensure Rhino is running with the server script active
   - Open a terminal in your project directory
   - Activate your virtual environment if used
   - Run: `python rhino_client_deluxe.py`
   - You should see a confirmation of successful connection

### 3. Optional: Creating a Rhino Command

To start the server easily within Rhino:

1. Create `PythonBridgeCommand.py` in your Rhino scripts folder:
   - Typically located at `%APPDATA%\McNeel\Rhinoceros\8.0\scripts\`
   - Copy the command script code (provided below) into this file

2. Run the command in Rhino:
   - Type `PythonBridge` in Rhino's command line
   - The server should start automatically

## Script Code

### 1. Rhino Server Script (`rhino_bridge.py`)

```python
"""
Rhino Bridge - Simplified server for stable Python-Rhino communication.
Version: 2.0 (2025-03-13)

This script provides a reliable socket connection between Python and Rhino
with simplified error handling and robust object creation.
"""
import socket
import json
import sys
import traceback
import threading
import Rhino
import time

# Server configuration
HOST = '127.0.0.1'
PORT = 8888
SERVER_VERSION = "Bridge-2.0"
SERVER_START_TIME = time.strftime("%Y-%m-%d %H:%M:%S")

# Custom JSON encoder for handling .NET objects
class RhinoEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle .NET Version objects and other common types
        try:
            if hasattr(obj, 'ToString'):
                return str(obj)
            elif hasattr(obj, 'Count') and hasattr(obj, 'Item'):
                return [self.default(obj.Item[i]) for i in range(obj.Count)]
            else:
                return str(obj)  # Last resort: convert anything to string
        except:
            return str(obj)  # Absolute fallback
        
        # Let the base class handle other types
        return super(RhinoEncoder, self).default(obj)

def handle_client(conn, addr):
    """Handle individual client connections"""
    print(f"Connection established from {addr}")
    
    try:
        while True:
            # Receive command
            data = conn.recv(4096)
            if not data:
                break
                
            # Parse the command
            try:
                command_obj = json.loads(data.decode('utf-8'))
                cmd_type = command_obj.get('type', '')
                cmd_data = command_obj.get('data', {})
                
                print(f"Received command: {cmd_type}")
                result = {'status': 'error', 'message': 'Unknown command'}
                
                # Process different command types
                if cmd_type == 'ping':
                    result = {
                        'status': 'success',
                        'message': 'Rhino is connected',
                        'data': {
                            'version': str(Rhino.RhinoApp.Version),
                            'has_active_doc': Rhino.RhinoDoc.ActiveDoc is not None,
                            'server_version': SERVER_VERSION,
                            'server_start_time': SERVER_START_TIME,
                            'script_path': __file__
                        }
                    }
                
                elif cmd_type == 'create_sphere':
                    # SIMPLIFIED APPROACH: Just create the sphere without complex checks
                    try:
                        center_x = cmd_data.get('center_x', 0)
                        center_y = cmd_data.get('center_y', 0)
                        center_z = cmd_data.get('center_z', 0)
                        radius = cmd_data.get('radius', 5.0)
                        
                        doc = Rhino.RhinoDoc.ActiveDoc
                        if not doc:
                            raise Exception("No active Rhino document")
                            
                        # Create the sphere directly
                        center = Rhino.Geometry.Point3d(center_x, center_y, center_z)
                        sphere = Rhino.Geometry.Sphere(center, radius)
                        
                        # Convert to a brep for better display
                        brep = sphere.ToBrep()
                        
                        # Add to document, ignoring the return value
                        doc.Objects.AddBrep(brep)
                        
                        # Force view update
                        doc.Views.Redraw()
                        
                        result = {
                            'status': 'success',
                            'message': f'Sphere created at ({center_x}, {center_y}, {center_z}) with radius {radius}'
                        }
                    except Exception as e:
                        result = {
                            'status': 'error', 
                            'message': f'Sphere creation error: {str(e)}',
                            'traceback': traceback.format_exc()
                        }
                
                elif cmd_type == 'refresh_view':
                    try:
                        doc = Rhino.RhinoDoc.ActiveDoc
                        if doc:
                            doc.Views.Redraw()
                            result = {'status': 'success', 'message': 'Views refreshed'}
                        else:
                            result = {'status': 'error', 'message': 'No active document'}
                    except Exception as e:
                        result = {'status': 'error', 'message': f'Refresh error: {str(e)}'}
                
                elif cmd_type == 'run_script':
                    script = cmd_data.get('script', '')
                    if script:
                        # Capture print output
                        old_stdout = sys.stdout
                        from io import StringIO
                        captured_output = StringIO()
                        sys.stdout = captured_output
                        
                        try:
                            # Execute the script
                            exec(script)
                            result = {
                                'status': 'success',
                                'message': 'Script executed',
                                'data': {'output': captured_output.getvalue()}
                            }
                        except Exception as e:
                            result = {
                                'status': 'error', 
                                'message': f'Script execution error: {str(e)}',
                                'data': {'traceback': traceback.format_exc()}
                            }
                        finally:
                            sys.stdout = old_stdout
                    else:
                        result = {'status': 'error', 'message': 'No script provided'}
                
                # Send the result back using the custom encoder
                conn.sendall(json.dumps(result, cls=RhinoEncoder).encode('utf-8'))
                
            except json.JSONDecodeError:
                conn.sendall(json.dumps({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }).encode('utf-8'))
            except Exception as e:
                print(f"Error processing command: {str(e)}")
                traceback.print_exc()
                conn.sendall(json.dumps({
                    'status': 'error',
                    'message': f'Server error: {str(e)}',
                    'traceback': traceback.format_exc()
                }, cls=RhinoEncoder).encode('utf-8'))
    except Exception as e:
        print(f"Connection error: {str(e)}")
    finally:
        print(f"Connection closed with {addr}")
        conn.close()

def start_server():
    """Start the socket server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
            s.listen()
            print(f"Server started on {HOST}:{PORT}")
            print("Waiting for connections...")
            
            try:
                while True:
                    conn, addr = s.accept()
                    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
            except KeyboardInterrupt:
                print("Server shutting down...")
            except Exception as e:
                print(f"Server error: {str(e)}")
                traceback.print_exc()
        except Exception as e:
            print(f"Failed to bind to {HOST}:{PORT}. Error: {str(e)}")
            print("Try closing any other running instances of this script or check if another program is using this port.")

# Display server information
print("\n========== RHINO BRIDGE ==========")
print(f"Version: {SERVER_VERSION}")
print(f"Started: {SERVER_START_TIME}")
print(f"File: {__file__}")
print("===================================\n")

# Start the server in a background thread to keep Rhino responsive
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

print("Rhino Bridge started!")
print(f"Listening on {HOST}:{PORT}")
print("Keep this script running in Rhino's Python editor")
print("The server will run until you close this script or Rhino")
```

### 2. Python Client Script (`rhino_client_deluxe.py`)

```python
"""
Rhino Client Deluxe - Interactive client for Rhino connection.
Version: 1.0 (2025-03-13)

This script provides an interactive terminal for connecting to and
controlling Rhino from external Python scripts.
"""
import os
import sys
import json
import socket
import time
from typing import Dict, Any, Optional, List, Tuple

class RhinoClient:
    """Client for maintaining an interactive connection with Rhino."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        """Initialize the interactive Rhino client."""
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.command_history: List[str] = []
    
    def connect(self) -> bool:
        """Establish connection to the Rhino socket server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Test connection with ping and verify server version
            response = self.send_command('ping')
            if response and response.get('status') == 'success':
                server_data = response.get('data', {})
                print(f"\n✅ Connected to Rhino {server_data.get('version', 'unknown')}")
                print(f"🔌 Server: {server_data.get('server_version', 'unknown')}")
                print(f"📂 Script: {server_data.get('script_path', 'unknown')}")
                print(f"⏰ Started: {server_data.get('server_start_time', 'unknown')}")
                
                # Ensure we're connected to the Deluxe server
                if 'Deluxe' not in server_data.get('server_version', ''):
                    print("\n⚠️ WARNING: Not connected to RhinoServerDeluxe!")
                    print("You may experience errors with spheres and other commands.")
                    print("Please run rhino_server_deluxe.py in Rhino's Python editor.")
                
                # Add an immediate view refresh to ensure everything is visible
                self.refresh_view()
                return True
                
            print("\n❌ Connection test failed")
            self.disconnect()
            return False
            
        except Exception as e:
            print(f"\n❌ Connection error: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close the connection to Rhino."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        self.connected = False
        print("\nDisconnected from Rhino")
    
    def send_command(self, cmd_type: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to the Rhino server and return the response."""
        if not self.connected or not self.socket:
            print("❌ Not connected to Rhino")
            return {'status': 'error', 'message': 'Not connected to Rhino'}
        
        try:
            # Create command
            command = {
                'type': cmd_type,
                'data': data or {}
            }
            
            # Send command
            self.socket.sendall(json.dumps(command).encode('utf-8'))
            
            # Receive response
            response = self.socket.recv(8192)
            return json.loads(response.decode('utf-8'))
            
        except Exception as e:
            print(f"❌ Error sending command: {str(e)}")
            # Don't disconnect automatically to allow for retry
            return {'status': 'error', 'message': f'Command error: {str(e)}'}
    
    def create_sphere(self, x: float, y: float, z: float, radius: float) -> Dict[str, Any]:
        """Create a sphere in Rhino."""
        data = {
            'center_x': x,
            'center_y': y,
            'center_z': z,
            'radius': radius
        }
        result = self.send_command('create_sphere', data)
        
        # Always refresh view after creating geometry
        if result.get('status') == 'success':
            self.refresh_view()
            
        return result
    
    def run_script(self, script: str) -> Dict[str, Any]:
        """Run a Python script in Rhino."""
        result = self.send_command('run_script', {'script': script})
        
        # Always refresh view after running a script
        if result.get('status') == 'success':
            self.refresh_view()
            
        return result
    
    def refresh_view(self) -> Dict[str, Any]:
        """Refresh the Rhino viewport."""
        return self.send_command('refresh_view')
    
    def add_to_history(self, command: str) -> None:
        """Add a command to the history."""
        if command and command not in ['', 'exit', 'help']:
            self.command_history.append(command)
            if len(self.command_history) > 100:  # Limit history size
                self.command_history.pop(0)

def print_help() -> None:
    """Print help information about available commands."""
    print("\n=== Available Commands ===")
    print("sphere <x> <y> <z> <radius> - Create a sphere")
    print("script <python_code> - Run Python code in Rhino")
    print("refresh - Refresh the Rhino viewport")
    print("history - Show command history")
    print("ping - Test connection to Rhino")
    print("help - Show this help message")
    print("exit - Close the connection and exit")
    print("\nExample: sphere 10 20 0 5")
    print("Example: script import Rhino; print(f\"Current doc: {Rhino.RhinoDoc.ActiveDoc.Name}\")")

def main() -> None:
    """Run the interactive Rhino client."""
    print("\n========== RHINO CLIENT DELUXE ==========")
    print("Version: 1.0 (2025-03-13)")
    print("==========================================\n")
    
    print("This script provides an interactive connection to Rhino.")
    print("Make sure 'rhino_server_deluxe.py' is running in Rhino's Python editor.")
    
    # Create client
    client = RhinoClient()
    
    # Connect to Rhino
    if not client.connect():
        print("\nFailed to connect to Rhino. Make sure the server script is running.")
        return
    
    print_help()
    
    # Command loop
    try:
        while True:
            command = input("\nrhino> ").strip()
            
            if not command:
                continue
                
            if command.lower() == 'exit':
                break
                
            if command.lower() == 'help':
                print_help()
                continue
                
            if command.lower() == 'ping':
                response = client.send_command('ping')
                if response.get('status') == 'success':
                    print(f"Connection active! Rhino version: {response.get('data', {}).get('version', 'unknown')}")
                else:
                    print(f"Ping failed: {response.get('message', 'Unknown error')}")
                client.add_to_history(command)
                continue
            
            # View refresh command
            if command.lower() == 'refresh':
                response = client.refresh_view()
                if response.get('status') == 'success':
                    print("✅ Viewport refreshed")
                else:
                    print(f"❌ Refresh failed: {response.get('message', 'Unknown error')}")
                client.add_to_history(command)
                continue
                
            # Command history
            if command.lower() == 'history':
                if client.command_history:
                    print("\n=== Command History ===")
                    for i, cmd in enumerate(client.command_history):
                        print(f"{i+1}. {cmd}")
                else:
                    print("No command history yet.")
                continue
            
            # Parse sphere command: sphere <x> <y> <z> <radius>
            if command.lower().startswith('sphere '):
                try:
                    parts = command.split()
                    if len(parts) != 5:
                        print("❌ Invalid sphere command. Format: sphere <x> <y> <z> <radius>")
                        continue
                    
                    x, y, z, radius = map(float, parts[1:])
                    response = client.create_sphere(x, y, z, radius)
                    
                    if response.get('status') == 'success':
                        print(f"✅ {response.get('message', 'Sphere created successfully')}")
                    else:
                        print(f"❌ Sphere creation failed: {response.get('message', 'Unknown error')}")
                        if response.get('traceback'):
                            print("\nError details:")
                            print(response.get('traceback'))
                            print("\nTroubleshooting tip: Make sure you're running rhino_server_deluxe.py in Rhino")
                    
                    client.add_to_history(command)
                except ValueError:
                    print("❌ Invalid parameters. All values must be numbers.")
                continue
            
            # Handle script command: script <python code>
            if command.lower().startswith('script '):
                script = command[7:]  # Remove 'script ' prefix
                response = client.run_script(script)
                
                if response.get('status') == 'success':
                    print("\n=== Script Output ===")
                    output = response.get('data', {}).get('output', 'No output')
                    if output.strip():
                        print(output)
                    else:
                        print("Script executed successfully (no output)")
                else:
                    print(f"❌ Script error: {response.get('message', 'Unknown error')}")
                    if 'traceback' in response:
                        print("\n=== Error Traceback ===")
                        print(response['traceback'])
                
                client.add_to_history(command)
                continue
            
            print(f"❌ Unknown command: {command}")
            print("Type 'help' for available commands")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
```

### 3. Rhino Command Script (`PythonBridgeCommand.py`)

```python
"""Rhino-Python Bridge Command
Creates a custom Rhino command to start the Python socket server.
"""
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import System
import os

__commandname__ = "PythonBridge"

def RunCommand(is_interactive):
    """Run the PythonBridge command, which starts the socket server for Python connections."""
    # Create path to the user's Documents folder (reliable location)
    docs_folder = System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments)
    projects_folder = os.path.join(docs_folder, "CascadeProjects", "rhino_windsurf")
    
    # Path to the server script
    script_path = os.path.join(projects_folder, "rhino_bridge.py")
    
    # Check if the file exists at the default location
    if not os.path.exists(script_path):
        # If not found, ask the user for the file location
        filter = "Python Files (*.py)|*.py|All Files (*.*)|*.*||"
        script_path = rs.OpenFileName("Select the rhino_bridge.py script", filter)
        
        if not script_path:
            print("Operation canceled. No server script selected.")
            return Rhino.Commands.Result.Cancel
    
    # Run the script using Rhino's script runner
    Rhino.RhinoApp.RunScript("_-RunPythonScript \"" + script_path + "\"", False)
    
    print("Python Bridge server started!")
    print(f"Server script: {script_path}")
    print("You can now connect from external Python scripts")
    
    return Rhino.Commands.Result.Success

# This is needed for Rhino to recognize the command
if __name__ == "__main__":
    RunCommand(True)
```

## Using the Python-Rhino Bridge

### Basic Commands

Once the bridge is set up and both the server and client are running, you can interact with Rhino using these commands:

1. **Creating Spheres**:
   ```
   rhino> sphere <x> <y> <z> <radius>
   ```
   Example: `sphere 10 20 0 5`

2. **Running Python Scripts in Rhino**:
   ```
   rhino> script <python_code>
   ```
   Example: `script import Rhino; print(f"Rhino version: {Rhino.RhinoApp.Version}")`

3. **Refreshing the Viewport**:
   ```
   rhino> refresh
   ```

4. **Testing Connection**:
   ```
   rhino> ping
   ```

5. **Viewing Command History**:
   ```
   rhino> history
   ```

6. **Exiting the Client**:
   ```
   rhino> exit
   ```

### Advanced Usage: Multi-Statement Python Commands

You can run multiple Python statements in a single command by separating them with semicolons:

```
rhino> script import Rhino; import random; x = random.uniform(0,10); y = random.uniform(0,10); print(f"Random point: ({x}, {y})")
```

For more complex scripts, you can use Python's block syntax with proper indentation:

```
rhino> script if True:
    import Rhino
    import random
    for i in range(3):
        x = random.uniform(0, 10)
        y = random.uniform(0, 10)
        z = random.uniform(0, 10)
        print(f"Point {i+1}: ({x}, {y}, {z})")
```

### Creating Complex Geometry

To create more complex geometry, you can write scripts that leverage the full power of RhinoCommon:

```
rhino> script import Rhino; doc = Rhino.RhinoDoc.ActiveDoc; curve = Rhino.Geometry.Circle(Rhino.Geometry.Plane.WorldXY, 10).ToNurbsCurve(); doc.Objects.AddCurve(curve); doc.Views.Redraw()
```

## Troubleshooting

### Common Issues and Solutions

1. **Connection Refused**:
   - Ensure Rhino is running with the server script active
   - Check if another instance of the server is already running on port 8888
   - Try restarting Rhino and the server script

2. **Geometry Not Appearing**:
   - Use the `refresh` command to force a viewport update
   - Make sure you have an active document open in Rhino
   - Check for error messages in the command response

3. **Script Execution Errors**:
   - Verify your Python syntax is correct
   - Make sure you're using RhinoCommon API methods correctly
   - Check the error traceback for specific issues

4. **Server Warning in Client**:
   - The "Not connected to RhinoServerDeluxe" warning can be ignored if using the Bridge version
   - Make sure you're using compatible versions of the server and client scripts

### Extending the Bridge

You can extend the functionality of the bridge by:

1. Adding new command types to the server script
2. Implementing additional geometry creation methods in the client
3. Creating specialized scriptlets for common tasks

## Conclusion

The Python-Rhino Bridge provides a powerful way to control Rhino programmatically from external Python scripts. Whether you're automating modeling tasks, integrating with other tools, or building custom workflows, this bridge offers a flexible and robust connection between Python and Rhino.

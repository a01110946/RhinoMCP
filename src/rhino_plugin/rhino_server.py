"""
Rhino Bridge Server - Socket server for Rhino-Python communication.

This module implements a socket server that runs inside Rhino's Python editor and
allows external Python processes to communicate with and control Rhino.

Version: 1.0 (2025-03-13)
"""
from typing import Dict, Any, Optional, List, Tuple, Union
import socket
import json
import sys
import traceback
import threading
import time

# Import Rhino-specific modules
try:
    import Rhino
    import rhinoscriptsyntax as rs
    import scriptcontext as sc
except ImportError:
    print("Warning: Rhino modules not found. This script must run inside Rhino's Python editor.")

# Server configuration
HOST = '127.0.0.1'
PORT = 8888
SERVER_VERSION = "RhinoMCP-1.0"
SERVER_START_TIME = time.strftime("%Y-%m-%d %H:%M:%S")


class RhinoEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling Rhino and .NET objects.
    
    Args:
        None
        
    Returns:
        Encoded JSON string
    """
    def default(self, obj: Any) -> Any:
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


def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """Handle individual client connections.
    
    Args:
        conn: Socket connection object
        addr: Client address tuple (host, port)
        
    Returns:
        None
    """
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
                result: Dict[str, Any] = {'status': 'error', 'message': 'Unknown command'}
                
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
                
                elif cmd_type == 'create_curve':
                    try:
                        # Extract points from the command data
                        points_data = cmd_data.get('points', [])
                        
                        # Check if we have enough points for a curve
                        if len(points_data) < 2:
                            raise ValueError("At least 2 points are required to create a curve")
                            
                        # Convert point data to Rhino points
                        points = []
                        for pt in points_data:
                            x = pt.get('x', 0.0)
                            y = pt.get('y', 0.0)
                            z = pt.get('z', 0.0)
                            points.append(Rhino.Geometry.Point3d(x, y, z))
                        
                        # Create the curve
                        doc = Rhino.RhinoDoc.ActiveDoc
                        if not doc:
                            raise Exception("No active Rhino document")
                            
                        # Create a NURBS curve
                        curve = Rhino.Geometry.Curve.CreateInterpolatedCurve(points, 3)
                        
                        if not curve:
                            raise Exception("Failed to create curve")
                            
                        # Add to document
                        id = doc.Objects.AddCurve(curve)
                        
                        # Force view update
                        doc.Views.Redraw()
                        
                        result = {
                            'status': 'success',
                            'message': f'Curve created with {len(points)} points',
                            'data': {
                                'id': str(id),
                                'point_count': len(points)
                            }
                        }
                    except Exception as e:
                        result = {
                            'status': 'error', 
                            'message': f'Curve creation error: {str(e)}',
                            'traceback': traceback.format_exc()
                        }
                
                elif cmd_type == 'refresh_view':
                    try:
                        doc = Rhino.RhinoDoc.ActiveDoc
                        if not doc:
                            raise Exception("No active Rhino document")
                        
                        doc.Views.Redraw()
                        result = {
                            'status': 'success',
                            'message': 'View refreshed'
                        }
                    except Exception as e:
                        result = {
                            'status': 'error', 
                            'message': f'View refresh error: {str(e)}'
                        }
                
                elif cmd_type == 'run_script':
                    try:
                        script = cmd_data.get('script', '')
                        if not script:
                            raise ValueError("Empty script")
                        
                        # Execute the script in Rhino's Python context
                        locals_dict = {}
                        exec(script, globals(), locals_dict)
                        
                        # Return the result if available
                        script_result = locals_dict.get('result', None)
                        result = {
                            'status': 'success',
                            'message': 'Script executed successfully',
                            'data': {
                                'result': script_result
                            }
                        }
                    except Exception as e:
                        result = {
                            'status': 'error', 
                            'message': f'Script execution error: {str(e)}',
                            'traceback': traceback.format_exc()
                        }
                
                # Send the result back to the client
                response = json.dumps(result, cls=RhinoEncoder)
                conn.sendall(response.encode('utf-8'))
                
            except json.JSONDecodeError:
                conn.sendall(json.dumps({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }).encode('utf-8'))
                
    except Exception as e:
        print(f"Connection error: {str(e)}")
    finally:
        print(f"Connection closed with {addr}")
        conn.close()


def start_server() -> None:
    """Start the socket server.
    
    Args:
        None
        
    Returns:
        None
        
    Raises:
        OSError: If the server fails to start
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
            s.listen(5)
            print(f"Rhino Bridge started! Listening on {HOST}:{PORT}")
            print(f"Server version: {SERVER_VERSION}")
            print(f"Start time: {SERVER_START_TIME}")
            
            while True:
                conn, addr = s.accept()
                # Handle each client in a separate thread
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
                
        except OSError as e:
            if e.errno == 10048:  # Address already in use
                print("Error: Address already in use. Is the Rhino Bridge already running?")
            else:
                print(f"Socket error: {str(e)}")
        except Exception as e:
            print(f"Server error: {str(e)}")
            traceback.print_exc()


if __name__ == "__main__":
    # Only start if running directly in Rhino's Python editor
    if 'Rhino' in sys.modules:
        start_server()
    else:
        print("This script should be run inside Rhino's Python editor.")

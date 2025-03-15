#!/usr/bin/env python
"""
Test script to create a curve in Rhino using the RhinoClient.

This script connects directly to the Rhino Bridge and creates a NURBS curve
with three points.
"""
import sys
import json
from rhino_mcp.rhino_client import RhinoClient

def main():
    """Connect to Rhino and create a curve."""
    # Create a client and connect to Rhino
    client = RhinoClient(host="127.0.0.1", port=8888)
    connected = client.connect()
    
    if not connected:
        print("Failed to connect to Rhino Bridge")
        return 1
    
    print("Connected to Rhino Bridge")
    
    # Create points for the curve
    points = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 10, "y": 10, "z": 0},
        {"x": 20, "y": 0, "z": 0}
    ]
    
    # Format the command as expected by the Rhino Bridge server
    command = {
        "type": "create_curve",
        "data": {
            "points": points
        }
    }
    
    # Send the command to Rhino
    try:
        # The client.send_command method adds the type field, so we need to extract our data
        response = client.send_command("create_curve", {"points": points})
        print(f"Response from Rhino: {response}")
        return 0
    except Exception as e:
        print(f"Error creating curve: {e}")
        return 1
    finally:
        # Clean up
        client.disconnect()

if __name__ == "__main__":
    sys.exit(main())

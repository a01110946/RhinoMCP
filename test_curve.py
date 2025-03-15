#!/usr/bin/env python
"""
Test script to create a NURBS curve in Rhino via RhinoMCP.
"""
from src.rhino_mcp.rhino_client import RhinoClient, Point3d

def main():
    # Create a client and connect to Rhino
    client = RhinoClient()
    if client.connect():
        print("Connected to Rhino Bridge")
        
        # Create the points as dictionaries (Point3d is a TypedDict)
        points = [
            {"x": 0, "y": 0, "z": 0},
            {"x": 10, "y": 10, "z": 0},
            {"x": 20, "y": 0, "z": 0}
        ]
        
        # Send the curve creation command
        result = client.create_curve(points)
        
        # Print the result
        print("Curve creation result:", result)
        
        # Disconnect
        client.disconnect()
    else:
        print("Failed to connect to Rhino Bridge")

if __name__ == "__main__":
    main()

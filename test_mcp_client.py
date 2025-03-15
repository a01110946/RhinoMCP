#!/usr/bin/env python
"""
Test MCP Client - Simple websocket client to test the RhinoMCP server.

This script simulates a client (like Claude) making requests to the RhinoMCP server
using the Model Context Protocol.
"""
import asyncio
import json
import websockets
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-test-client")

# MCP server URI
MCP_URI = "ws://127.0.0.1:5000"

async def test_mcp_connection() -> bool:
    """Test connection to the MCP server.
    
    Returns:
        bool: True if the test passes, False otherwise
    """
    try:
        async with websockets.connect(MCP_URI) as websocket:
            logger.info(f"Connected to MCP server at {MCP_URI}")
            
            # Send initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            }
            
            await websocket.send(json.dumps(initialize_request))
            logger.info(f"Sent initialize request")
            
            # Receive response
            response = await websocket.recv()
            initialize_response = json.loads(response)
            logger.info(f"Received initialize response: {json.dumps(initialize_response, indent=2)}")
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await websocket.send(json.dumps(initialized_notification))
            logger.info(f"Sent initialized notification")
            
            # There may be a capabilities notification response, try to receive it
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                capabilities_notification = json.loads(response)
                logger.info(f"Received notification: {json.dumps(capabilities_notification, indent=2)}")
            except asyncio.TimeoutError:
                logger.info("No notification received (as expected)")
            
            # Request tools list
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            await websocket.send(json.dumps(tools_request))
            logger.info(f"Sent tools/list request")
            
            # Receive tools list response
            response = await websocket.recv()
            tools_response = json.loads(response)
            logger.info(f"Received tools list: {json.dumps(tools_response, indent=2)}")
            
            # Create a curve using the MCP protocol
            create_curve_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "rhino_create_curve",
                "params": {
                    "points": [
                        {"x": 0, "y": 0, "z": 30},
                        {"x": 10, "y": 10, "z": 30},
                        {"x": 20, "y": 0, "z": 30}
                    ]
                }
            }
            
            await websocket.send(json.dumps(create_curve_request))
            logger.info(f"Sent curve creation request")
            
            # Receive curve creation response
            response = await websocket.recv()
            curve_response = json.loads(response)
            logger.info(f"Received curve creation response: {json.dumps(curve_response, indent=2)}")
            
            # Check if curve was created successfully
            if "result" in curve_response and "status" in curve_response["result"]:
                status = curve_response["result"]["status"]
                logger.info(f"Curve creation status: {status}")
                if status == "success":
                    logger.info("✅ Test passed: Curve created successfully!")
                    return True
                else:
                    logger.error(f"❌ Test failed: {curve_response['result']['message']}")
                    return False
            else:
                logger.error("❌ Test failed: Invalid response format")
                return False
            
    except Exception as e:
        logger.error(f"❌ Error connecting to MCP server: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())

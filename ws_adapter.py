#!/usr/bin/env python
"""
WebSocket adapter for connecting Windsurf to the RhinoMCP server.

This script forwards messages between Windsurf and the RhinoMCP server,
acting as an adapter layer that handles the WebSocket connection.
"""
import asyncio
import json
import sys
import websockets
from typing import Dict, Any, Optional, List
import logging
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ws_adapter.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("ws-adapter")

# Target RhinoMCP server URL
TARGET_URL = "ws://127.0.0.1:5000"

async def forward_messages():
    """Forward messages between stdin/stdout and the WebSocket server."""
    try:
        logger.info(f"Connecting to RhinoMCP server at {TARGET_URL}")
        async with websockets.connect(TARGET_URL) as websocket:
            logger.info("Connected to RhinoMCP server")
            
            # Start tasks for handling stdin->websocket and websocket->stdout
            stdin_task = asyncio.create_task(forward_stdin_to_websocket(websocket))
            ws_task = asyncio.create_task(forward_websocket_to_stdout(websocket))
            
            # Wait for either task to complete (or fail)
            done, pending = await asyncio.wait(
                [stdin_task, ws_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                
            # Check for exceptions
            for task in done:
                try:
                    task.result()
                except Exception as e:
                    logger.error(f"Task error: {str(e)}")
                    
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        
async def forward_stdin_to_websocket(websocket):
    """Forward messages from stdin to the WebSocket server."""
    loop = asyncio.get_event_loop()
    while True:
        # Read a line from stdin (non-blocking)
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            logger.info("End of stdin, closing connection")
            break
            
        # Parse and forward the message
        try:
            message = line.strip()
            logger.debug(f"Sending to WS: {message}")
            await websocket.send(message)
        except Exception as e:
            logger.error(f"Error forwarding stdin to WebSocket: {str(e)}")
            break

async def forward_websocket_to_stdout(websocket):
    """Forward messages from the WebSocket server to stdout."""
    try:
        async for message in websocket:
            logger.debug(f"Received from WS: {message}")
            # Write to stdout and flush
            print(message, flush=True)
    except ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error forwarding WebSocket to stdout: {str(e)}")

if __name__ == "__main__":
    try:
        # Run the message forwarding loop
        asyncio.run(forward_messages())
    except KeyboardInterrupt:
        logger.info("Adapter terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)

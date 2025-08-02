#!/usr/bin/env python3
"""
Test WebSocket connection to identify the issue
"""
import asyncio
import websockets
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection"""
    try:
        # Get a valid token first
        import requests
        
        # Login to get a token
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "walkingstatue",
                "password": "Igaegeus@8803"
            }
        )
        
        if login_response.status_code != 200:
            logger.error(f"Failed to login: {login_response.status_code}")
            logger.error(login_response.text)
            return False
        
        token = login_response.json()["access_token"]
        logger.info("✓ Successfully obtained access token")
        
        # Test WebSocket connection
        bot_id = "c8c0470a-bbb4-4a75-952b-102203d866de"  # From the test
        ws_url = f"ws://localhost:8000/api/ws/chat/{bot_id}?token={token}"
        
        logger.info(f"Attempting to connect to: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            logger.info("✓ WebSocket connection established")
            
            # Wait for connection confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                logger.info(f"✓ Received connection confirmation: {message}")
                
                # Send a ping
                ping_message = {
                    "type": "ping",
                    "timestamp": "2025-08-02T07:54:30.000Z"
                }
                await websocket.send(json.dumps(ping_message))
                logger.info("✓ Sent ping message")
                
                # Wait for pong
                pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_message = json.loads(pong_response)
                logger.info(f"✓ Received pong: {pong_message}")
                
                # Send typing indicator
                typing_message = {
                    "type": "typing",
                    "data": {"is_typing": True}
                }
                await websocket.send(json.dumps(typing_message))
                logger.info("✓ Sent typing indicator")
                
                # Wait a bit to see if we get any responses
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        message = json.loads(response)
                        logger.info(f"Received message: {message}")
                except asyncio.TimeoutError:
                    logger.info("No more messages received (timeout)")
                
                return True
                
            except asyncio.TimeoutError:
                logger.error("✗ Timeout waiting for WebSocket response")
                return False
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"✗ WebSocket connection closed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ WebSocket test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run the WebSocket test"""
    logger.info("="*60)
    logger.info("TESTING WEBSOCKET CONNECTION")
    logger.info("="*60)
    
    success = await test_websocket_connection()
    
    if success:
        logger.info("\n🎉 WebSocket test PASSED!")
    else:
        logger.error("\n❌ WebSocket test FAILED!")
        logger.info("\nThis explains why the frontend WebSocket is not connecting.")

if __name__ == "__main__":
    asyncio.run(main())
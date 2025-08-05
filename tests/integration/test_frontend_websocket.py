#!/usr/bin/env python3
"""
Test WebSocket connection from frontend perspective
"""
import asyncio
import websockets
import json
import logging
import sys
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_frontend_websocket():
    """Test WebSocket connection as the frontend would"""
    try:
        # Login to get a token (same as frontend would do)
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "walkingstatue",
                "password": "Igaegeus@8803"
            }
        )
        
        if login_response.status_code != 200:
            logger.error(f"Failed to login: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        logger.info("✓ Successfully obtained access token")
        
        # Test health check first (as frontend does)
        try:
            health_response = requests.get("http://localhost:8000/health", timeout=5)
            if health_response.ok:
                logger.info("✓ Backend health check passed")
            else:
                logger.warning(f"Backend health check failed: {health_response.status_code}")
        except Exception as e:
            logger.warning(f"Backend health check failed: {e}")
        
        # Test WebSocket connection (as frontend would)
        bot_id = "c8c0470a-bbb4-4a75-952b-102203d866de"
        ws_url = f"ws://localhost:8000/api/ws/chat/{bot_id}?token={token}"
        
        logger.info(f"Attempting WebSocket connection to: {ws_url.replace(token, '[TOKEN]')}")
        
        # Test connection with timeout (similar to frontend)
        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("✓ WebSocket connection established")
                
                # Wait for connection confirmation (as frontend expects)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message = json.loads(response)
                    
                    if message.get("type") == "connection_established":
                        logger.info("✓ Received connection confirmation")
                        logger.info(f"  Bot: {message['data']['bot_name']}")
                        logger.info(f"  Connection ID: {message['data']['connection_id']}")
                        
                        # Test ping/pong (as frontend does for health checks)
                        ping_msg = {
                            "type": "ping",
                            "timestamp": "2025-08-02T07:54:30.000Z"
                        }
                        await websocket.send(json.dumps(ping_msg))
                        logger.info("✓ Sent ping message")
                        
                        # Wait for pong
                        pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        pong_message = json.loads(pong_response)
                        
                        if pong_message.get("type") == "pong":
                            logger.info("✓ Received pong response")
                            
                            # Test typing indicator (as frontend does)
                            typing_msg = {
                                "type": "typing",
                                "data": {"is_typing": True}
                            }
                            await websocket.send(json.dumps(typing_msg))
                            logger.info("✓ Sent typing indicator")
                            
                            # Stop typing
                            stop_typing_msg = {
                                "type": "typing",
                                "data": {"is_typing": False}
                            }
                            await websocket.send(json.dumps(stop_typing_msg))
                            logger.info("✓ Sent stop typing indicator")
                            
                            return True
                        else:
                            logger.error(f"✗ Expected pong, got: {pong_message}")
                            return False
                    else:
                        logger.error(f"✗ Expected connection_established, got: {message}")
                        return False
                        
                except asyncio.TimeoutError:
                    logger.error("✗ Timeout waiting for connection confirmation")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("✗ WebSocket connection timeout")
            return False
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"✗ WebSocket connection closed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ WebSocket connection error: {e}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run the frontend WebSocket test"""
    logger.info("="*60)
    logger.info("TESTING FRONTEND WEBSOCKET CONNECTION")
    logger.info("="*60)
    
    success = await test_frontend_websocket()
    
    if success:
        logger.info("\n🎉 Frontend WebSocket test PASSED!")
        logger.info("The WebSocket connection works correctly from frontend perspective.")
    else:
        logger.error("\n❌ Frontend WebSocket test FAILED!")
        logger.info("This indicates an issue with the WebSocket setup.")

if __name__ == "__main__":
    asyncio.run(main())
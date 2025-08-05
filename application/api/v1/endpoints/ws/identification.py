import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from application.core.logging import get_logger
from application.core.dependencies import mongo_manager, connection_manager

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/identify")
async def media_identification_websocket(
    websocket: WebSocket,
    mongodb_manager = Depends(mongo_manager)
):
    """WebSocket endpoint for real-time media identification."""
    connection_id = None
    ws_manager = connection_manager()
    
    try:
        # Connect and get connection ID
        connection_id = await ws_manager.connect(websocket)
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Send initial connection confirmation
        await ws_manager.send_msg(
            {
                "type": "connected",
                "message": "WebSocket connection established!",
                "connection_id": connection_id
            },
            connection_id
        )
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                #logger.info(f"Received identification request: {message}")
                
                # Validate request structure
                if "type" not in message:
                    await ws_manager.send_err_msg(
                        connection_id,
                        "Missing 'type' field in request"
                    )
                    continue
                
                request_type = message["type"]
                
                if request_type == "text_query":
                    await _handle_frame_data(message, connection_id, mongodb_manager, ws_manager)
                    
                elif request_type == "audio_stream":
                    await _handle_audio_chunk(message, connection_id, mongodb_manager, ws_manager)
                    
                elif request_type == "ping":
                    await _handle_ping(connection_id, ws_manager)
                    
                else:
                    print(message)
                    # await ws_manager.send_err_msg(
                    #     connection_id,
                    #     f"Unknown request type: {request_type}"
                    # )

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                await ws_manager.send_err_msg(
                    connection_id,
                    "Invalid JSON format"
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                if not ws_manager.is_connected(connection_id):
                    break
                pass

    except WebSocketDisconnect:
        # Gracefully handle WebSocket disconnection
        pass
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if connection_id:
            ws_manager.disconnect(connection_id)


async def _handle_frame_data(
    message: Dict[str, Any],
    connection_id: str,
    mongodb_manager,
    ws_manager
):
    try:
        pass
    except Exception as e:
        logger.error(f"Error in text identification: {e}")
        await ws_manager.send_err_msg(
            connection_id,
            f"Text identification failed: {str(e)}"
        )


async def _handle_audio_chunk(
    message: Dict[str, Any],
    connection_id: str,
    mongodb_manager,
    ws_manager
):
    try:
        pass
    except Exception as e:
        logger.error(f"Error in audio identification: {e}")
        await ws_manager.send_err_msg(
            connection_id,
            f"Audio identification failed: {str(e)}"
        )


async def _handle_ping(connection_id: str, ws_manager):
    """Handle ping requests to keep connection alive."""
    try:
        await ws_manager.send_msg(
            {
                "status": "pong",
                "message": "Connection_alive",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            connection_id
        )
    except Exception as e:
        logger.error(f"Error handling ping: {e}")
        await ws_manager.send_err_msg(
            connection_id,
            f"Ping failed: {str(e)}"
        ) 
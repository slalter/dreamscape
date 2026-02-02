"""WebSocket API for real-time communication between frontend and backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.world import MessageType, WSMessage
from app.services.llm_service import LLMService
from app.services.world_state import WorldStateManager

logger = logging.getLogger(__name__)
router = APIRouter()


class SessionManager:
    """Manages active WebSocket sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(self, session_id: str, websocket: WebSocket) -> Session:
        world_state = WorldStateManager()
        llm_service = LLMService(world_state)
        session = Session(
            session_id=session_id,
            websocket=websocket,
            world_state=world_state,
            llm_service=llm_service,
        )
        self._sessions[session_id] = session
        return session

    def remove_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)


class Session:
    """A single user session with world state and LLM service."""

    def __init__(
        self,
        session_id: str,
        websocket: WebSocket,
        world_state: WorldStateManager,
        llm_service: LLMService,
    ) -> None:
        self.session_id = session_id
        self.websocket = websocket
        self.world_state = world_state
        self.llm_service = llm_service
        self._processing = False

    async def send(self, msg_type: MessageType, data: dict[str, Any]) -> None:
        """Send a message to the client."""
        message = WSMessage(type=msg_type, data=data)
        await self.websocket.send_json(message.model_dump(mode="json"))

    async def process_input(self, text: str) -> None:
        """Process user input through the LLM and send results."""
        if self._processing:
            await self.send(MessageType.STATUS, {"message": "Still processing previous request..."})
            return

        self._processing = True
        try:
            await self.send(MessageType.STATUS, {"message": "Imagining your world..."})

            self.world_state.increment_turn()
            actions = await self.llm_service.process_user_input(text)

            if actions:
                await self.send(MessageType.STATUS, {"message": f"Building {len(actions)} elements..."})

            for i, action in enumerate(actions):
                action_type = action.get("type", "")
                action_data = action.get("data", {})

                if action_type == "object_created":
                    await self.send(MessageType.OBJECT_CREATED, action_data)
                elif action_type == "object_modified":
                    await self.send(MessageType.OBJECT_MODIFIED, action_data)
                elif action_type == "object_removed":
                    await self.send(MessageType.OBJECT_REMOVED, action_data)
                elif action_type == "environment_updated":
                    await self.send(MessageType.ENVIRONMENT_UPDATED, action_data)
                elif action_type == "terrain_created":
                    await self.send(MessageType.TERRAIN_CREATED, action_data)
                elif action_type == "narration":
                    await self.send(MessageType.NARRATION, action_data)
                elif action_type == "model_uploaded":
                    await self.send(MessageType.MODEL_UPLOADED, action_data)
                elif action_type == "error":
                    await self.send(MessageType.ERROR, action_data)

                # Small delay between actions for visual effect
                await asyncio.sleep(0.1)

            cost = self.llm_service.cost_tracker.summary()
            await self.send(MessageType.STATUS, {
                "message": "Ready",
                "cost": cost,
            })

        except Exception as e:
            logger.exception("Error processing input")
            await self.send(MessageType.ERROR, {"message": str(e)})
        finally:
            self._processing = False


session_manager = SessionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """Main WebSocket endpoint for a dreamscape session."""
    await websocket.accept()
    session = session_manager.create_session(session_id, websocket)
    logger.info("Session started: %s", session_id)

    try:
        # Send initial world state
        await session.send(MessageType.WORLD_STATE, session.world_state.to_dict())
        await session.send(MessageType.STATUS, {"message": "Ready. Describe what you see..."})

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "user_input":
                text = data.get("data", {}).get("text", "")
                if text.strip():
                    asyncio.create_task(session.process_input(text))

    except WebSocketDisconnect:
        logger.info("Session disconnected: %s", session_id)
    except Exception:
        logger.exception("WebSocket error for session %s", session_id)
    finally:
        session_manager.remove_session(session_id)

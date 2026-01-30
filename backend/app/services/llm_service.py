"""LLM service - interfaces with OpenAI API to generate world content."""

from __future__ import annotations

import json
import logging
from typing import Any

import openai

from app.config import config
from app.services.world_state import WorldStateManager
from app.tools.definitions import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Dreamscape World Builder, an AI that creates immersive 3D environments in real-time based on what the user describes. You exist inside a 3D game engine.

Your role:
1. Listen to what the user describes or imagines
2. Use your tools to build that world around them
3. Be creative and detailed - don't just place basic shapes, compose rich scenes
4. Narrate the experience to set mood and atmosphere
5. Maintain continuity with what's already in the scene

Guidelines:
- ALWAYS use the narrate tool to describe what you're creating
- Create multiple objects to build a scene (e.g., a forest needs many trees, bushes, rocks)
- Vary object positions, sizes, rotations to make scenes feel natural
- Use the environment tool to set appropriate lighting and atmosphere
- Use terrain to create ground surfaces
- Think about composition - place things at different distances and heights
- Be responsive to the user's imagination - if they describe something, build it
- If the user describes movement or a new area, create new content ahead of them
- Use children objects to build complex composite shapes (e.g., a tree = cylinder trunk + sphere canopy)

Object naming: Use descriptive snake_case names like 'tall_pine_1', 'mossy_boulder', 'red_barn'.

Position guide: The user starts at (0, 1.6, 0). Y=0 is ground level. Spread objects naturally in the XZ plane."""


class LLMService:
    """Handles communication with the OpenAI API for world generation."""

    def __init__(self, world_state: WorldStateManager) -> None:
        self._client = openai.OpenAI(api_key=config.llm.api_key)
        self._world_state = world_state
        self._conversation_history: list[dict[str, Any]] = []

    async def process_user_input(self, user_text: str) -> list[dict[str, Any]]:
        """Process user input and return a list of world actions."""
        context = self._world_state.get_context_summary()

        user_message = f"[Current World State]\n{context}\n\n[User says]: {user_text}"

        self._conversation_history.append(
            {"role": "user", "content": user_message}
        )

        # Keep conversation manageable
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-16:]

        actions: list[dict[str, Any]] = []

        try:
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self._conversation_history,
            ]

            response = self._client.chat.completions.create(
                model=config.llm.model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            choice = response.choices[0]
            message = choice.message

            # Build assistant message for history
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": message.content}
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,  # type: ignore[union-attr]
                            "arguments": tc.function.arguments,  # type: ignore[union-attr]
                        },
                    }
                    for tc in message.tool_calls
                ]

            self._conversation_history.append(assistant_msg)

            # Process tool calls
            if message.tool_calls:
                for tc in message.tool_calls:
                    input_data: dict[str, Any] = json.loads(tc.function.arguments)  # type: ignore[union-attr]
                    action = self._execute_tool(tc.function.name, input_data)  # type: ignore[union-attr]
                    actions.append(action)

                    # Add tool result to conversation
                    self._conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": f"Success: {action['type']} - {action.get('name', '')}",
                    })

                # Check if the model wants to continue
                if choice.finish_reason == "tool_calls":
                    continuation = await self._continue_generation()
                    actions.extend(continuation)

        except openai.APIError as e:
            logger.error("OpenAI API error: %s", e)
            actions.append({
                "type": "error",
                "data": {"message": f"AI service error: {e}"},
            })

        return actions

    async def _continue_generation(self, depth: int = 0) -> list[dict[str, Any]]:
        """Continue generating if the model has more tool calls."""
        if depth >= 5:
            return []

        actions: list[dict[str, Any]] = []

        try:
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self._conversation_history,
            ]

            response = self._client.chat.completions.create(
                model=config.llm.model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            choice = response.choices[0]
            message = choice.message

            assistant_msg: dict[str, Any] = {"role": "assistant", "content": message.content}
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,  # type: ignore[union-attr]
                            "arguments": tc.function.arguments,  # type: ignore[union-attr]
                        },
                    }
                    for tc in message.tool_calls
                ]

            self._conversation_history.append(assistant_msg)

            if message.tool_calls:
                for tc in message.tool_calls:
                    input_data: dict[str, Any] = json.loads(tc.function.arguments)  # type: ignore[union-attr]
                    action = self._execute_tool(tc.function.name, input_data)  # type: ignore[union-attr]
                    actions.append(action)

                    self._conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": f"Success: {action['type']} - {action.get('name', '')}",
                    })

                if choice.finish_reason == "tool_calls":
                    continuation = await self._continue_generation(depth + 1)
                    actions.extend(continuation)

        except openai.APIError as e:
            logger.error("OpenAI API continuation error: %s", e)

        return actions

    def _execute_tool(self, name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call and return the action."""
        if name == "create_object":
            obj = self._world_state.create_object(input_data)
            return {
                "type": "object_created",
                "name": obj.name,
                "data": obj.model_dump(mode="json"),
            }
        elif name == "modify_object":
            obj = self._world_state.modify_object(input_data)
            if obj:
                return {
                    "type": "object_modified",
                    "name": obj.name,
                    "data": obj.model_dump(mode="json"),
                }
            return {"type": "error", "data": {"message": f"Object not found: {input_data.get('name')}"}}
        elif name == "remove_object":
            obj_name = input_data["name"]
            success = self._world_state.remove_object(obj_name)
            return {
                "type": "object_removed" if success else "error",
                "name": obj_name,
                "data": {"name": obj_name, "success": success},
            }
        elif name == "set_environment":
            env = self._world_state.update_environment(input_data)
            return {
                "type": "environment_updated",
                "data": env.model_dump(mode="json"),
            }
        elif name == "create_terrain":
            terrain = self._world_state.add_terrain(input_data)
            return {
                "type": "terrain_created",
                "data": terrain.model_dump(mode="json"),
            }
        elif name == "narrate":
            text = input_data["text"]
            self._world_state.add_narrative(text)
            return {
                "type": "narration",
                "data": {"text": text},
            }
        else:
            return {"type": "error", "data": {"message": f"Unknown tool: {name}"}}

    def reset(self) -> None:
        """Reset conversation history."""
        self._conversation_history = []

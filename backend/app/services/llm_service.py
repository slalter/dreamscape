"""LLM service - interfaces with Claude API to generate world content."""

from __future__ import annotations

import logging
from typing import Any

import anthropic

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
    """Handles communication with the Claude API for world generation."""

    def __init__(self, world_state: WorldStateManager) -> None:
        self._client = anthropic.Anthropic(api_key=config.llm.api_key)
        self._world_state = world_state
        self._conversation_history: list[dict[str, Any]] = []

    async def process_user_input(self, user_text: str) -> list[dict[str, Any]]:
        """Process user input and return a list of world actions.

        Returns a list of dicts with 'type' and 'data' keys representing
        actions to apply to the world.
        """
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
            response = self._client.messages.create(
                model=config.llm.model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=self._conversation_history,  # type: ignore[arg-type]
            )

            # Process the response - may have multiple tool uses
            assistant_content: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    action = self._execute_tool(block.name, block.input)
                    actions.append(action)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Success: {action['type']} - {action.get('name', '')}",
                    })

            self._conversation_history.append({
                "role": "assistant",
                "content": assistant_content,
            })

            # If there were tool uses, send results back and check for more
            if tool_results:
                self._conversation_history.append({
                    "role": "user",
                    "content": tool_results,
                })

                # Check if the model wants to continue
                if response.stop_reason == "tool_use":
                    continuation = await self._continue_generation()
                    actions.extend(continuation)

        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
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
            response = self._client.messages.create(
                model=config.llm.model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=self._conversation_history,  # type: ignore[arg-type]
            )

            assistant_content: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    action = self._execute_tool(block.name, block.input)
                    actions.append(action)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Success: {action['type']} - {action.get('name', '')}",
                    })

            self._conversation_history.append({
                "role": "assistant",
                "content": assistant_content,
            })

            if tool_results:
                self._conversation_history.append({
                    "role": "user",
                    "content": tool_results,
                })
                if response.stop_reason == "tool_use":
                    continuation = await self._continue_generation(depth + 1)
                    actions.extend(continuation)

        except anthropic.APIError as e:
            logger.error("Claude API continuation error: %s", e)

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

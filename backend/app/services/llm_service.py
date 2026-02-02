"""LLM service - interfaces with OpenAI API to generate world content."""

from __future__ import annotations

import json
import logging
from typing import Any

import openai

from app.config import config
from app.services.code_executor import execute_model_code
from app.services.world_state import WorldStateManager
from app.tools.definitions import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Dreamscape World Builder, an AI that creates immersive 3D environments in real-time based on what the user describes. You exist inside a 3D game engine.

Your role:
1. Listen to what the user describes or imagines
2. Use your tools to build that world around them
3. Be creative and detailed — compose rich, multi-part scenes
4. Narrate the experience to set mood and atmosphere
5. Maintain continuity with what's already in the scene

## CRITICAL: Building High-Quality Objects

You MUST build objects by composing multiple primitive shapes using the **children** array. NEVER try to represent a complex object with a single primitive — it will look terrible.

### How to build creatures and complex objects:

**Example — a turtle:**
- Body: a flattened sphere (scale y=0.5) with dark green color, roughness=0.8
- Shell top: a half-sphere on top, darker green, slightly metallic
- Head: a small sphere positioned forward, lighter green
- 4 legs: small cylinders positioned at corners, angled outward
- Tail: a tiny cone at the back
- Eyes: two tiny black spheres on the head

**Example — a tree:**
- Trunk: brown cylinder (radius_top slightly smaller than radius_bottom)
- Canopy: 2-3 overlapping green spheres at different heights for fullness
- Roots: small flattened cylinders at the base

### Material Guidelines (act as "skins"):
- Use **color** creatively — vary hue across children for realism (e.g., lighter belly, darker back)
- Use **roughness** to convey texture: rough=0.9 for bark/stone, rough=0.3 for wet/shiny surfaces
- Use **metalness** sparingly: 0.0 for organic, 0.1-0.3 for slightly reflective, 0.8+ for metal
- Use **emissive** for glowing elements (eyes, lava, magic effects)
- NEVER use flat_shading=true for organic/natural objects — it makes them look faceted and ugly
- NEVER use wireframe=true unless the user specifically asks for it

### Geometry Guidelines:
- Use **sphere** with high segments (32x16) for smooth organic shapes
- Use **cylinder** for limbs, trunks, pillars
- Use **box** for buildings, furniture, blocky objects
- Use **cone** for pointed features (horns, roofs, tails)
- Use **torus** for rings, wheels, halos
- AVOID using 'custom' geometry with raw vertices — the results are almost always ugly low-poly triangles. Use composed primitives instead.
- When building an animal or creature, use AT LEAST 6-10 children to get a recognizable shape

## Advanced: Generating High-Quality Models with Code

For the BEST quality objects (realistic creatures, detailed vehicles, organic shapes), use the
`generate_3d_model` tool instead of `create_object`. This lets you write Python code using the
`trimesh` library to create proper 3D meshes with:
- Smooth, detailed geometry using icospheres, boolean operations, and vertex manipulation
- Per-face or per-vertex coloring for realistic skin/surface appearance
- PBR texture maps generated with PIL/Pillow for photorealistic materials
- Proper UV mapping for detailed surface patterns

Use `generate_3d_model` when the user asks for creatures, characters, vehicles, or anything
that needs to look realistic. Use `create_object` for simpler scene elements (buildings,
trees, rocks, terrain features) where composed primitives are sufficient.

### General Guidelines:
- ALWAYS use the narrate tool to describe what you're creating
- ALWAYS respond to user questions via narrate — never ignore them
- Create multiple objects to build a scene (e.g., a forest needs many trees, bushes, rocks)
- Vary object positions, sizes, rotations to make scenes feel natural
- Use the environment tool to set appropriate lighting and atmosphere
- Use terrain to create ground surfaces
- Think about composition — place things at different distances and heights
- Be responsive to the user's imagination
- If the user describes movement or a new area, create new content ahead of them

Object naming: Use descriptive snake_case names like 'tall_pine_1', 'mossy_boulder', 'red_barn'.

Position guide: The user starts at (0, 1.6, 0). Y=0 is ground level. Spread objects naturally in the XZ plane."""


# Pricing per million tokens (GPT-5.1)
INPUT_COST_PER_M = 1.25
OUTPUT_COST_PER_M = 10.0


class CostTracker:
    """Tracks cumulative API usage costs for a session."""

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1

    @property
    def total_cost(self) -> float:
        input_cost = (self.total_input_tokens / 1_000_000) * INPUT_COST_PER_M
        output_cost = (self.total_output_tokens / 1_000_000) * OUTPUT_COST_PER_M
        return input_cost + output_cost

    def summary(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
        }


class LLMService:
    """Handles communication with the OpenAI API for world generation."""

    def __init__(self, world_state: WorldStateManager) -> None:
        self._client = openai.OpenAI(api_key=config.llm.api_key)
        self._world_state = world_state
        self._conversation_history: list[dict[str, Any]] = []
        self.cost_tracker = CostTracker()

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
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            # Track costs
            if response.usage:
                self.cost_tracker.record(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                logger.info(
                    "API cost: $%.4f (session total: $%.4f)",
                    (response.usage.prompt_tokens / 1_000_000 * INPUT_COST_PER_M +
                     response.usage.completion_tokens / 1_000_000 * OUTPUT_COST_PER_M),
                    self.cost_tracker.total_cost,
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
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            if response.usage:
                self.cost_tracker.record(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
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
        elif name == "generate_3d_model":
            code = input_data["code"]
            object_name = input_data.get("object_name", "generated_model")
            position = input_data.get("position", {"x": 0, "y": 0, "z": 0})
            scale = input_data.get("scale", {"x": 1, "y": 1, "z": 1})
            rotation = input_data.get("rotation", {"x": 0, "y": 0, "z": 0})

            result = execute_model_code(code)

            if result["success"] and result["files"]:
                file_info = result["files"][0]
                return {
                    "type": "model_uploaded",
                    "name": object_name,
                    "data": {
                        "name": object_name,
                        "url": file_info["url"],
                        "position": position,
                        "scale": scale,
                        "rotation": rotation,
                    },
                }
            else:
                error_msg = result.get("error", "Unknown error during model generation")
                return {
                    "type": "error",
                    "data": {"message": f"Model generation failed: {error_msg}"},
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

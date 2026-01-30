"""World state management - tracks all objects, environment, and narrative."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import uuid4

from app.schemas.world import (
    AnimationParams,
    Color,
    EnvironmentSettings,
    GeometryParams,
    MaterialParams,
    PhysicsParams,
    TerrainParams,
    Vec3,
    WorldObject,
    WorldState,
)

logger = logging.getLogger(__name__)


class WorldStateManager:
    """Manages the complete state of a world session."""

    def __init__(self) -> None:
        self._state = WorldState()

    @property
    def state(self) -> WorldState:
        return self._state

    @property
    def object_count(self) -> int:
        return len(self._state.objects)

    def create_object(self, data: dict[str, Any]) -> WorldObject:
        """Create a new object from LLM tool call data."""
        name = data["name"]
        if name in self._state.objects:
            # Append unique suffix
            name = f"{name}_{uuid4().hex[:6]}"

        obj = WorldObject(
            name=name,
            description=data.get("description", ""),
            position=_parse_vec3(data.get("position")),
            rotation=_parse_vec3(data.get("rotation")),
            scale=_parse_vec3(data.get("scale"), default=Vec3(x=1, y=1, z=1)),
            geometry=_parse_geometry(data.get("geometry", {})),
            material=_parse_material(data.get("material", {})),
            physics=_parse_physics(data.get("physics", {})),
            animation=_parse_animation(data.get("animation", {})),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

        # Handle children recursively
        for child_data in data.get("children", []):
            child_data.setdefault("name", f"{name}_child_{uuid4().hex[:4]}")
            child_data.setdefault("geometry", {"type": "box"})
            child = WorldObject(
                name=child_data["name"],
                description=child_data.get("description", ""),
                position=_parse_vec3(child_data.get("position")),
                rotation=_parse_vec3(child_data.get("rotation")),
                scale=_parse_vec3(child_data.get("scale"), default=Vec3(x=1, y=1, z=1)),
                geometry=_parse_geometry(child_data.get("geometry", {})),
                material=_parse_material(child_data.get("material", {})),
                physics=_parse_physics(child_data.get("physics", {})),
                animation=_parse_animation(child_data.get("animation", {})),
            )
            obj.children.append(child)

        self._state.objects[name] = obj
        logger.info("Created object: %s", name)
        return obj

    def modify_object(self, data: dict[str, Any]) -> Optional[WorldObject]:
        """Modify an existing object."""
        name = data.get("name", "")
        obj = self._state.objects.get(name)
        if not obj:
            logger.warning("Object not found for modification: %s", name)
            return None

        if "position" in data and data["position"]:
            obj.position = _parse_vec3(data["position"])
        if "rotation" in data and data["rotation"]:
            obj.rotation = _parse_vec3(data["rotation"])
        if "scale" in data and data["scale"]:
            obj.scale = _parse_vec3(data["scale"], default=Vec3(x=1, y=1, z=1))
        if "material" in data and data["material"]:
            mat = data["material"]
            if "color" in mat:
                obj.material.color = _parse_color(mat["color"])
            if "metalness" in mat:
                obj.material.metalness = mat["metalness"]
            if "roughness" in mat:
                obj.material.roughness = mat["roughness"]
            if "opacity" in mat:
                obj.material.opacity = mat["opacity"]
            if "transparent" in mat:
                obj.material.transparent = mat["transparent"]
        if "animation" in data and data["animation"]:
            obj.animation = _parse_animation(data["animation"])

        logger.info("Modified object: %s", name)
        return obj

    def remove_object(self, name: str) -> bool:
        """Remove an object by name."""
        if name in self._state.objects:
            del self._state.objects[name]
            logger.info("Removed object: %s", name)
            return True
        logger.warning("Object not found for removal: %s", name)
        return False

    def update_environment(self, data: dict[str, Any]) -> EnvironmentSettings:
        """Update environment settings."""
        env = self._state.environment
        if "sky_color" in data:
            env.sky_color = _parse_color(data["sky_color"])
        if "fog_enabled" in data:
            env.fog_enabled = data["fog_enabled"]
        if "fog_color" in data:
            env.fog_color = _parse_color(data["fog_color"])
        if "fog_near" in data:
            env.fog_near = data["fog_near"]
        if "fog_far" in data:
            env.fog_far = data["fog_far"]
        if "ambient_light_color" in data:
            env.ambient_light_color = _parse_color(data["ambient_light_color"])
        if "ambient_light_intensity" in data:
            env.ambient_light_intensity = data["ambient_light_intensity"]
        if "sun_color" in data:
            env.sun_color = _parse_color(data["sun_color"])
        if "sun_intensity" in data:
            env.sun_intensity = data["sun_intensity"]
        if "sun_position" in data:
            env.sun_position = _parse_vec3(data["sun_position"])
        if "time_of_day" in data:
            env.time_of_day = data["time_of_day"]
        logger.info("Updated environment")
        return env

    def add_terrain(self, data: dict[str, Any]) -> TerrainParams:
        """Add terrain to the world."""
        terrain = TerrainParams(
            type=data.get("type", "flat"),
            size=data.get("size", 100.0),
            height=data.get("height", 10.0),
            color=_parse_color(data.get("color", {})),
            segments=data.get("segments", 32),
            seed=data.get("seed"),
        )
        self._state.terrain.append(terrain)
        logger.info("Added terrain: %s", terrain.type)
        return terrain

    def add_narrative(self, text: str) -> None:
        """Add narrative text to history."""
        self._state.narrative_history.append(text)
        # Keep only last 20 entries to manage context
        if len(self._state.narrative_history) > 20:
            self._state.narrative_history = self._state.narrative_history[-20:]

    def increment_turn(self) -> None:
        """Increment the turn counter."""
        self._state.turn_count += 1

    def get_context_summary(self) -> str:
        """Generate a summary of the current world state for LLM context."""
        lines: list[str] = []
        lines.append(f"Turn: {self._state.turn_count}")
        lines.append(f"Objects in scene: {len(self._state.objects)}")

        if self._state.objects:
            lines.append("\nCurrent objects:")
            for name, obj in self._state.objects.items():
                pos = obj.position
                lines.append(
                    f"  - {name}: {obj.description or obj.geometry.type.value} "
                    f"at ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})"
                )

        if self._state.terrain:
            lines.append(f"\nTerrain: {', '.join(t.type for t in self._state.terrain)}")

        env = self._state.environment
        lines.append(f"\nEnvironment: {env.time_of_day}, sun intensity {env.sun_intensity}")

        if self._state.narrative_history:
            lines.append("\nRecent narrative:")
            for entry in self._state.narrative_history[-5:]:
                lines.append(f"  \"{entry}\"")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize full state."""
        return self._state.model_dump(mode="json")

    def reset(self) -> None:
        """Reset to empty world."""
        self._state = WorldState()


def _parse_vec3(data: Optional[dict[str, Any]], default: Optional[Vec3] = None) -> Vec3:
    if not data:
        return default or Vec3()
    return Vec3(
        x=float(data.get("x", 0)),
        y=float(data.get("y", 0)),
        z=float(data.get("z", 0)),
    )


def _parse_color(data: Optional[dict[str, Any]]) -> Color:
    if not data:
        return Color()
    return Color(
        r=float(data.get("r", 1)),
        g=float(data.get("g", 1)),
        b=float(data.get("b", 1)),
    )


def _parse_geometry(data: dict[str, Any]) -> GeometryParams:
    return GeometryParams(**{k: v for k, v in data.items() if v is not None})


def _parse_material(data: dict[str, Any]) -> MaterialParams:
    parsed: dict[str, Any] = {}
    for key, val in data.items():
        if val is None:
            continue
        if key in ("color", "emissive"):
            parsed[key] = _parse_color(val)
        else:
            parsed[key] = val
    return MaterialParams(**parsed)


def _parse_physics(data: dict[str, Any]) -> PhysicsParams:
    return PhysicsParams(**{k: v for k, v in data.items() if v is not None})


def _parse_animation(data: dict[str, Any]) -> AnimationParams:
    parsed: dict[str, Any] = {}
    for key, val in data.items():
        if val is None:
            continue
        if key == "axis":
            parsed[key] = _parse_vec3(val)
        else:
            parsed[key] = val
    return AnimationParams(**parsed)

"""Pydantic schemas for world objects and messages."""

from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class GeometryType(str, Enum):
    """Supported geometry types."""

    BOX = "box"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    TORUS = "torus"
    PLANE = "plane"
    CUSTOM = "custom"  # Procedural vertex data


class Vec3(BaseModel):
    """3D vector."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Color(BaseModel):
    """RGB color (0-1 range)."""

    r: float = 1.0
    g: float = 1.0
    b: float = 1.0


class GeometryParams(BaseModel):
    """Parameters for geometry generation."""

    type: GeometryType = GeometryType.BOX
    # Box
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    # Sphere
    radius: Optional[float] = None
    width_segments: Optional[int] = None
    height_segments: Optional[int] = None
    # Cylinder/Cone
    radius_top: Optional[float] = None
    radius_bottom: Optional[float] = None
    # Torus
    tube: Optional[float] = None
    radial_segments: Optional[int] = None
    tubular_segments: Optional[int] = None
    # Custom procedural geometry
    vertices: Optional[list[float]] = None
    indices: Optional[list[int]] = None
    normals: Optional[list[float]] = None
    uvs: Optional[list[float]] = None


class MaterialParams(BaseModel):
    """Material definition."""

    color: Color = Field(default_factory=Color)
    emissive: Optional[Color] = None
    emissive_intensity: float = 0.0
    metalness: float = 0.0
    roughness: float = 0.5
    opacity: float = 1.0
    transparent: bool = False
    wireframe: bool = False
    flat_shading: bool = False


class PhysicsParams(BaseModel):
    """Physics properties."""

    has_gravity: bool = True
    is_static: bool = True
    mass: float = 1.0
    friction: float = 0.5
    restitution: float = 0.3


class AnimationParams(BaseModel):
    """Simple animation definition."""

    type: str = "none"  # "rotate", "bob", "orbit", "none"
    speed: float = 1.0
    axis: Vec3 = Field(default_factory=lambda: Vec3(x=0, y=1, z=0))
    amplitude: float = 1.0


class WorldObject(BaseModel):
    """A complete object in the world."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    position: Vec3 = Field(default_factory=Vec3)
    rotation: Vec3 = Field(default_factory=Vec3)
    scale: Vec3 = Field(default_factory=lambda: Vec3(x=1, y=1, z=1))
    geometry: GeometryParams = Field(default_factory=GeometryParams)
    material: MaterialParams = Field(default_factory=MaterialParams)
    physics: PhysicsParams = Field(default_factory=PhysicsParams)
    animation: AnimationParams = Field(default_factory=AnimationParams)
    children: list["WorldObject"] = Field(default_factory=lambda: [])
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSettings(BaseModel):
    """Global environment settings."""

    sky_color: Color = Field(default_factory=lambda: Color(r=0.53, g=0.81, b=0.92))
    ground_color: Color = Field(default_factory=lambda: Color(r=0.34, g=0.49, b=0.27))
    fog_color: Optional[Color] = None
    fog_near: float = 50.0
    fog_far: float = 200.0
    fog_enabled: bool = False
    ambient_light_color: Color = Field(default_factory=lambda: Color(r=0.4, g=0.4, b=0.4))
    ambient_light_intensity: float = 0.6
    sun_color: Color = Field(default_factory=lambda: Color(r=1.0, g=0.95, b=0.8))
    sun_intensity: float = 1.0
    sun_position: Vec3 = Field(default_factory=lambda: Vec3(x=50, y=100, z=50))
    time_of_day: str = "day"  # "dawn", "day", "dusk", "night"


class TerrainParams(BaseModel):
    """Terrain generation parameters."""

    type: str = "flat"  # "flat", "hills", "mountains", "water"
    size: float = 100.0
    height: float = 10.0
    color: Color = Field(default_factory=lambda: Color(r=0.34, g=0.49, b=0.27))
    segments: int = 32
    seed: Optional[int] = None


# WebSocket message types

class MessageType(str, Enum):
    """WebSocket message types."""

    USER_INPUT = "user_input"
    OBJECT_CREATED = "object_created"
    OBJECT_MODIFIED = "object_modified"
    OBJECT_REMOVED = "object_removed"
    ENVIRONMENT_UPDATED = "environment_updated"
    TERRAIN_CREATED = "terrain_created"
    NARRATION = "narration"
    STATUS = "status"
    ERROR = "error"
    WORLD_STATE = "world_state"
    MODEL_UPLOADED = "model_uploaded"


class WSMessage(BaseModel):
    """WebSocket message envelope."""

    type: MessageType
    data: dict[str, Any] = Field(default_factory=dict)


class WorldState(BaseModel):
    """Complete state of the world."""

    objects: dict[str, WorldObject] = Field(default_factory=dict)
    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)
    terrain: list[TerrainParams] = Field(default_factory=list)
    narrative_history: list[str] = Field(default_factory=list)
    turn_count: int = 0


# Rebuild models with forward references
WorldObject.model_rebuild()

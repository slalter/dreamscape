"""Tests for Pydantic schemas."""

from __future__ import annotations

from uuid import UUID

from app.schemas.world import (
    Color,
    EnvironmentSettings,
    GeometryParams,
    GeometryType,
    MaterialParams,
    TerrainParams,
    Vec3,
    WorldObject,
    WorldState,
    WSMessage,
    MessageType,
)


class TestVec3:
    def test_defaults(self) -> None:
        v = Vec3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_custom_values(self) -> None:
        v = Vec3(x=1.5, y=2.0, z=-3.0)
        assert v.x == 1.5


class TestColor:
    def test_defaults_white(self) -> None:
        c = Color()
        assert c.r == 1.0
        assert c.g == 1.0
        assert c.b == 1.0


class TestGeometryParams:
    def test_default_box(self) -> None:
        g = GeometryParams()
        assert g.type == GeometryType.BOX

    def test_sphere(self) -> None:
        g = GeometryParams(type=GeometryType.SPHERE, radius=2.0)
        assert g.radius == 2.0

    def test_custom_with_vertices(self) -> None:
        g = GeometryParams(
            type=GeometryType.CUSTOM,
            vertices=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 1.0, 0.0],
            indices=[0, 1, 2],
        )
        assert g.vertices is not None
        assert len(g.vertices) == 9


class TestMaterialParams:
    def test_defaults(self) -> None:
        m = MaterialParams()
        assert m.metalness == 0.0
        assert m.roughness == 0.5
        assert m.opacity == 1.0
        assert m.transparent is False


class TestWorldObject:
    def test_creation(self) -> None:
        obj = WorldObject(name="test")
        assert isinstance(obj.id, UUID)
        assert obj.name == "test"
        assert obj.geometry.type == GeometryType.BOX
        assert obj.scale.x == 1.0

    def test_serialization(self) -> None:
        obj = WorldObject(name="box", description="A box")
        data = obj.model_dump(mode="json")
        assert data["name"] == "box"
        assert "geometry" in data
        assert "material" in data


class TestEnvironmentSettings:
    def test_defaults(self) -> None:
        env = EnvironmentSettings()
        assert env.time_of_day == "day"
        assert env.fog_enabled is False
        assert env.sun_intensity == 1.0


class TestTerrainParams:
    def test_defaults(self) -> None:
        t = TerrainParams()
        assert t.type == "flat"
        assert t.size == 100.0


class TestWorldState:
    def test_empty_state(self) -> None:
        state = WorldState()
        assert len(state.objects) == 0
        assert state.turn_count == 0

    def test_serialization_roundtrip(self) -> None:
        state = WorldState()
        data = state.model_dump(mode="json")
        restored = WorldState.model_validate(data)
        assert restored.turn_count == 0


class TestWSMessage:
    def test_message(self) -> None:
        msg = WSMessage(type=MessageType.STATUS, data={"message": "ok"})
        assert msg.type == MessageType.STATUS
        data = msg.model_dump(mode="json")
        assert data["type"] == "status"

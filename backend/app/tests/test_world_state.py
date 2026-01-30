"""Tests for world state management."""

from __future__ import annotations

import pytest

from app.services.world_state import WorldStateManager


@pytest.fixture
def manager() -> WorldStateManager:
    return WorldStateManager()


class TestCreateObject:
    def test_create_simple_object(self, manager: WorldStateManager) -> None:
        obj = manager.create_object({
            "name": "test_box",
            "description": "A test box",
            "geometry": {"type": "box", "width": 2, "height": 2, "depth": 2},
            "position": {"x": 1, "y": 0, "z": 0},
            "material": {"color": {"r": 1, "g": 0, "b": 0}},
        })
        assert obj.name == "test_box"
        assert obj.geometry.type.value == "box"
        assert obj.geometry.width == 2
        assert obj.position.x == 1
        assert obj.material.color.r == 1
        assert manager.object_count == 1

    def test_create_duplicate_name_gets_suffix(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "tree", "geometry": {"type": "cylinder"}})
        obj2 = manager.create_object({"name": "tree", "geometry": {"type": "sphere"}})
        assert obj2.name.startswith("tree_")
        assert manager.object_count == 2

    def test_create_object_with_children(self, manager: WorldStateManager) -> None:
        obj = manager.create_object({
            "name": "tree",
            "geometry": {"type": "cylinder", "height": 3, "radius_top": 0.2, "radius_bottom": 0.3},
            "children": [
                {
                    "name": "canopy",
                    "geometry": {"type": "sphere", "radius": 2},
                    "position": {"x": 0, "y": 3, "z": 0},
                    "material": {"color": {"r": 0.2, "g": 0.6, "b": 0.1}},
                }
            ],
        })
        assert len(obj.children) == 1
        assert obj.children[0].name == "canopy"

    def test_create_object_defaults(self, manager: WorldStateManager) -> None:
        obj = manager.create_object({"name": "minimal", "geometry": {"type": "box"}})
        assert obj.position.x == 0
        assert obj.scale.x == 1
        assert obj.material.color.r == 1
        assert obj.physics.is_static is True
        assert obj.animation.type == "none"

    def test_create_custom_geometry(self, manager: WorldStateManager) -> None:
        obj = manager.create_object({
            "name": "custom",
            "geometry": {
                "type": "custom",
                "vertices": [0, 0, 0, 1, 0, 0, 0.5, 1, 0],
                "indices": [0, 1, 2],
            },
        })
        assert obj.geometry.type.value == "custom"
        assert obj.geometry.vertices is not None
        assert len(obj.geometry.vertices) == 9


class TestModifyObject:
    def test_modify_position(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "box", "geometry": {"type": "box"}})
        result = manager.modify_object({"name": "box", "position": {"x": 5, "y": 3, "z": 1}})
        assert result is not None
        assert result.position.x == 5
        assert result.position.y == 3

    def test_modify_material(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "box", "geometry": {"type": "box"}})
        result = manager.modify_object({
            "name": "box",
            "material": {"color": {"r": 0, "g": 1, "b": 0}, "metalness": 0.8},
        })
        assert result is not None
        assert result.material.color.g == 1
        assert result.material.metalness == 0.8

    def test_modify_nonexistent_returns_none(self, manager: WorldStateManager) -> None:
        result = manager.modify_object({"name": "ghost"})
        assert result is None

    def test_modify_animation(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "spinner", "geometry": {"type": "box"}})
        result = manager.modify_object({
            "name": "spinner",
            "animation": {"type": "rotate", "speed": 2.0},
        })
        assert result is not None
        assert result.animation.type == "rotate"
        assert result.animation.speed == 2.0


class TestRemoveObject:
    def test_remove_existing(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "doomed", "geometry": {"type": "box"}})
        assert manager.remove_object("doomed") is True
        assert manager.object_count == 0

    def test_remove_nonexistent(self, manager: WorldStateManager) -> None:
        assert manager.remove_object("ghost") is False


class TestEnvironment:
    def test_update_environment(self, manager: WorldStateManager) -> None:
        env = manager.update_environment({
            "sky_color": {"r": 0.1, "g": 0.1, "b": 0.3},
            "fog_enabled": True,
            "fog_color": {"r": 0.5, "g": 0.5, "b": 0.5},
            "time_of_day": "night",
        })
        assert env.sky_color.r == 0.1
        assert env.fog_enabled is True
        assert env.time_of_day == "night"


class TestTerrain:
    def test_add_terrain(self, manager: WorldStateManager) -> None:
        terrain = manager.add_terrain({"type": "hills", "size": 200, "height": 15})
        assert terrain.type == "hills"
        assert terrain.size == 200
        assert len(manager.state.terrain) == 1


class TestNarrative:
    def test_add_narrative(self, manager: WorldStateManager) -> None:
        manager.add_narrative("The world awakens.")
        assert len(manager.state.narrative_history) == 1
        assert manager.state.narrative_history[0] == "The world awakens."

    def test_narrative_limit(self, manager: WorldStateManager) -> None:
        for i in range(25):
            manager.add_narrative(f"Entry {i}")
        assert len(manager.state.narrative_history) == 20


class TestContextSummary:
    def test_summary_includes_objects(self, manager: WorldStateManager) -> None:
        manager.create_object({
            "name": "big_rock",
            "geometry": {"type": "sphere"},
            "position": {"x": 5, "y": 0, "z": 10},
        })
        summary = manager.get_context_summary()
        assert "big_rock" in summary
        assert "5.0" in summary

    def test_summary_empty_world(self, manager: WorldStateManager) -> None:
        summary = manager.get_context_summary()
        assert "Objects in scene: 0" in summary


class TestSerialization:
    def test_to_dict(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "box", "geometry": {"type": "box"}})
        data = manager.to_dict()
        assert "objects" in data
        assert "environment" in data
        assert "box" in data["objects"]


class TestReset:
    def test_reset(self, manager: WorldStateManager) -> None:
        manager.create_object({"name": "box", "geometry": {"type": "box"}})
        manager.add_narrative("Hello")
        manager.reset()
        assert manager.object_count == 0
        assert len(manager.state.narrative_history) == 0

"""Tests for tool definitions."""

from __future__ import annotations

from app.tools.definitions import TOOL_DEFINITIONS


class TestToolDefinitions:
    def test_all_tools_have_required_fields(self) -> None:
        for tool in TOOL_DEFINITIONS:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert func["parameters"]["type"] == "object"

    def test_expected_tools_exist(self) -> None:
        names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        assert "create_object" in names
        assert "modify_object" in names
        assert "remove_object" in names
        assert "set_environment" in names
        assert "create_terrain" in names
        assert "narrate" in names

    def test_create_object_has_geometry_required(self) -> None:
        create_tool = next(t for t in TOOL_DEFINITIONS if t["function"]["name"] == "create_object")
        assert "geometry" in create_tool["function"]["parameters"]["required"]
        assert "name" in create_tool["function"]["parameters"]["required"]

    def test_narrate_has_text_required(self) -> None:
        narrate_tool = next(t for t in TOOL_DEFINITIONS if t["function"]["name"] == "narrate")
        assert "text" in narrate_tool["function"]["parameters"]["required"]

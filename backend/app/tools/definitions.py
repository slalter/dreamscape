"""Tool definitions for the LLM to manipulate the world.

These are Claude API tool definitions that allow the LLM to create,
modify, and remove objects in the 3D world.
"""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "create_object",
        "description": (
            "Create a new 3D object in the world. You can create simple parametric shapes "
            "(box, sphere, cylinder, cone, torus, plane) or custom procedural geometry by "
            "providing vertex data. Each object has geometry, material, physics, and animation "
            "properties. Be creative - vary colors, sizes, and positions to build rich scenes. "
            "You can create complex objects by using the children array to compose multiple shapes."
        ),
        "input_schema": {
            "type": "object",
            "required": ["name", "geometry"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique descriptive name for this object (e.g., 'old_oak_tree', 'red_barn')",
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what this object represents in the scene",
                },
                "position": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "X position (left/right)"},
                        "y": {"type": "number", "description": "Y position (up/down, 0 = ground)"},
                        "z": {"type": "number", "description": "Z position (forward/back)"},
                    },
                },
                "rotation": {
                    "type": "object",
                    "description": "Rotation in radians",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "z": {"type": "number"},
                    },
                },
                "scale": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "default": 1},
                        "y": {"type": "number", "default": 1},
                        "z": {"type": "number", "default": 1},
                    },
                },
                "geometry": {
                    "type": "object",
                    "required": ["type"],
                    "description": "Geometry definition. Use parametric types for simple shapes, or 'custom' with vertex data for novel geometry.",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["box", "sphere", "cylinder", "cone", "torus", "plane", "custom"],
                        },
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                        "depth": {"type": "number"},
                        "radius": {"type": "number"},
                        "radius_top": {"type": "number"},
                        "radius_bottom": {"type": "number"},
                        "tube": {"type": "number"},
                        "width_segments": {"type": "integer"},
                        "height_segments": {"type": "integer"},
                        "radial_segments": {"type": "integer"},
                        "tubular_segments": {"type": "integer"},
                        "vertices": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Flat array of vertex positions [x1,y1,z1, x2,y2,z2, ...] for custom geometry",
                        },
                        "indices": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Triangle indices for custom geometry",
                        },
                        "normals": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Vertex normals for custom geometry",
                        },
                        "uvs": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "UV coordinates for custom geometry",
                        },
                    },
                },
                "material": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "object",
                            "properties": {
                                "r": {"type": "number", "minimum": 0, "maximum": 1},
                                "g": {"type": "number", "minimum": 0, "maximum": 1},
                                "b": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                        },
                        "emissive": {
                            "type": "object",
                            "properties": {
                                "r": {"type": "number", "minimum": 0, "maximum": 1},
                                "g": {"type": "number", "minimum": 0, "maximum": 1},
                                "b": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                        },
                        "emissive_intensity": {"type": "number", "minimum": 0, "maximum": 5},
                        "metalness": {"type": "number", "minimum": 0, "maximum": 1},
                        "roughness": {"type": "number", "minimum": 0, "maximum": 1},
                        "opacity": {"type": "number", "minimum": 0, "maximum": 1},
                        "transparent": {"type": "boolean"},
                        "wireframe": {"type": "boolean"},
                        "flat_shading": {"type": "boolean"},
                    },
                },
                "physics": {
                    "type": "object",
                    "properties": {
                        "has_gravity": {"type": "boolean"},
                        "is_static": {"type": "boolean", "description": "If true, object doesn't move"},
                        "mass": {"type": "number"},
                        "friction": {"type": "number"},
                        "restitution": {"type": "number", "description": "Bounciness, 0-1"},
                    },
                },
                "animation": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["none", "rotate", "bob", "orbit"],
                            "description": "Animation type: rotate (spin), bob (up/down), orbit (circle around origin)",
                        },
                        "speed": {"type": "number"},
                        "axis": {
                            "type": "object",
                            "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                        },
                        "amplitude": {"type": "number"},
                    },
                },
                "children": {
                    "type": "array",
                    "description": "Child objects positioned relative to this parent, for building composite objects",
                    "items": {"type": "object"},
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization (e.g., 'vegetation', 'building', 'creature')",
                },
            },
        },
    },
    {
        "name": "modify_object",
        "description": (
            "Modify an existing object in the world. Provide the object name and any "
            "properties to update. Only provided fields will be changed."
        ),
        "input_schema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string", "description": "Name of the object to modify"},
                "position": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                },
                "rotation": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                },
                "scale": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                },
                "material": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "object",
                            "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                        },
                        "metalness": {"type": "number"},
                        "roughness": {"type": "number"},
                        "opacity": {"type": "number"},
                        "transparent": {"type": "boolean"},
                    },
                },
                "animation": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["none", "rotate", "bob", "orbit"]},
                        "speed": {"type": "number"},
                    },
                },
            },
        },
    },
    {
        "name": "remove_object",
        "description": "Remove an object from the world by name.",
        "input_schema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string", "description": "Name of the object to remove"},
            },
        },
    },
    {
        "name": "set_environment",
        "description": (
            "Change the global environment settings: sky color, fog, lighting, time of day. "
            "Use this to set mood and atmosphere."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sky_color": {
                    "type": "object",
                    "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                },
                "fog_enabled": {"type": "boolean"},
                "fog_color": {
                    "type": "object",
                    "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                },
                "fog_near": {"type": "number"},
                "fog_far": {"type": "number"},
                "ambient_light_color": {
                    "type": "object",
                    "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                },
                "ambient_light_intensity": {"type": "number", "minimum": 0, "maximum": 2},
                "sun_color": {
                    "type": "object",
                    "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                },
                "sun_intensity": {"type": "number", "minimum": 0, "maximum": 3},
                "sun_position": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}},
                },
                "time_of_day": {
                    "type": "string",
                    "enum": ["dawn", "day", "dusk", "night"],
                },
            },
        },
    },
    {
        "name": "create_terrain",
        "description": (
            "Create a terrain surface. Types: 'flat' (simple ground plane), 'hills' "
            "(rolling hills), 'mountains' (rugged terrain), 'water' (flat reflective surface)."
        ),
        "input_schema": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["flat", "hills", "mountains", "water"],
                },
                "size": {"type": "number", "description": "Size of terrain in world units"},
                "height": {"type": "number", "description": "Max height variation for hills/mountains"},
                "color": {
                    "type": "object",
                    "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                },
                "segments": {"type": "integer", "description": "Mesh resolution (higher = more detail)"},
                "seed": {"type": "integer", "description": "Random seed for reproducible terrain"},
            },
        },
    },
    {
        "name": "narrate",
        "description": (
            "Send narrative text to the user describing what's happening in the world. "
            "Use this to set the scene, describe events, or respond to the user's imagination. "
            "Keep it evocative but concise."
        ),
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string", "description": "Narrative text to display to the user"},
            },
        },
    },
]

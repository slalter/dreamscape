"""Tool definitions for the LLM to manipulate the world.

These are OpenAI function calling definitions that allow the LLM to create,
modify, and remove objects in the 3D world.
"""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_object",
            "description": (
                "Create a new 3D object in the world. You can create simple parametric shapes "
                "(box, sphere, cylinder, cone, torus, plane) or custom procedural geometry by "
                "providing vertex data. Each object has geometry, material, physics, and animation "
                "properties. Be creative - vary colors, sizes, and positions to build rich scenes. "
                "You can create complex objects by using the children array to compose multiple shapes."
            ),
            "parameters": {
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
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "z": {"type": "number"},
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
                                    "r": {"type": "number"},
                                    "g": {"type": "number"},
                                    "b": {"type": "number"},
                                },
                            },
                            "emissive": {
                                "type": "object",
                                "properties": {
                                    "r": {"type": "number"},
                                    "g": {"type": "number"},
                                    "b": {"type": "number"},
                                },
                            },
                            "emissive_intensity": {"type": "number"},
                            "metalness": {"type": "number"},
                            "roughness": {"type": "number"},
                            "opacity": {"type": "number"},
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
    },
    {
        "type": "function",
        "function": {
            "name": "modify_object",
            "description": (
                "Modify an existing object in the world. Provide the object name and any "
                "properties to update. Only provided fields will be changed."
            ),
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "remove_object",
            "description": "Remove an object from the world by name.",
            "parameters": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Name of the object to remove"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_environment",
            "description": (
                "Change the global environment settings: sky color, fog, lighting, time of day. "
                "Use this to set mood and atmosphere."
            ),
            "parameters": {
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
                    "ambient_light_intensity": {"type": "number"},
                    "sun_color": {
                        "type": "object",
                        "properties": {"r": {"type": "number"}, "g": {"type": "number"}, "b": {"type": "number"}},
                    },
                    "sun_intensity": {"type": "number"},
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
    },
    {
        "type": "function",
        "function": {
            "name": "create_terrain",
            "description": (
                "Create a terrain surface. Types: 'flat' (simple ground plane), 'hills' "
                "(rolling hills), 'mountains' (rugged terrain), 'water' (flat reflective surface)."
            ),
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "generate_3d_model",
            "description": (
                "Generate a high-quality 3D model by writing Python code that uses the 'trimesh' library. "
                "This is the PREFERRED method for creating detailed creatures, characters, vehicles, and "
                "complex objects that cannot be well-represented by composing simple primitives.\n\n"
                "Available in the execution environment:\n"
                "- `trimesh` - Full trimesh library for 3D mesh creation\n"
                "- `np` / `numpy` - NumPy for numerical operations\n"
                "- `save_model(mesh, name)` - Save a trimesh mesh as GLB file, returns the URL\n"
                "- `save_model_stl(mesh, name)` - Save as STL file, returns the URL\n\n"
                "Example for a turtle:\n"
                "```python\n"
                "import trimesh\n"
                "import numpy as np\n\n"
                "# Create shell (flattened sphere)\n"
                "shell = trimesh.creation.icosphere(subdivisions=3, radius=1.0)\n"
                "shell.vertices[:, 1] *= 0.4  # flatten\n"
                "shell.vertices[:, 1] += 0.3\n"
                "shell.visual.face_colors = [34, 120, 50, 255]  # dark green\n\n"
                "# Create body/belly\n"
                "belly = trimesh.creation.icosphere(subdivisions=3, radius=0.9)\n"
                "belly.vertices[:, 1] *= 0.25\n"
                "belly.visual.face_colors = [140, 180, 80, 255]\n\n"
                "# Head\n"
                "head = trimesh.creation.icosphere(subdivisions=2, radius=0.3)\n"
                "head.apply_translation([0.9, 0.2, 0])\n"
                "head.visual.face_colors = [100, 160, 60, 255]\n\n"
                "# Combine all parts\n"
                "turtle = trimesh.util.concatenate([shell, belly, head])\n"
                "save_model(turtle, 'turtle')\n"
                "```\n\n"
                "IMPORTANT: Always call save_model() or save_model_stl() at the end to make the model available. "
                "Use trimesh.creation functions (icosphere, cylinder, cone, box, etc.) and boolean operations "
                "for complex shapes.\n\n"
                "## Coloring and Texturing:\n"
                "- Simple: Set `mesh.visual.face_colors = [R, G, B, A]` (0-255 range) for uniform color\n"
                "- Per-face: Set `mesh.visual.face_colors = np.array([[R,G,B,A], ...])` with one color per face\n"
                "- Textured: Create a PIL Image, then apply as texture:\n"
                "```python\n"
                "from PIL import Image, ImageDraw\n"
                "import trimesh\n"
                "# Create a texture image\n"
                "img = Image.new('RGB', (512, 512), (34, 120, 50))\n"
                "draw = ImageDraw.Draw(img)\n"
                "# Draw patterns, scales, spots, etc.\n"
                "for i in range(0, 512, 32):\n"
                "    draw.line([(i, 0), (i, 512)], fill=(20, 80, 30), width=2)\n"
                "# Apply to mesh with UV mapping\n"
                "material = trimesh.visual.material.PBRMaterial(\n"
                "    baseColorTexture=img,\n"
                "    metallicFactor=0.0,\n"
                "    roughnessFactor=0.8\n"
                ")\n"
                "mesh.visual = trimesh.visual.TextureVisuals(material=material)\n"
                "```\n"
                "Also available: `Image`, `ImageDraw`, `ImageFilter` from PIL, and `scipy` for advanced operations."
            ),
            "parameters": {
                "type": "object",
                "required": ["code", "object_name"],
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code using trimesh to generate the 3D model. Must call save_model() at the end.",
                    },
                    "object_name": {
                        "type": "string",
                        "description": "Name for the object in the scene (snake_case)",
                    },
                    "position": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "z": {"type": "number"},
                        },
                    },
                    "scale": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "z": {"type": "number"},
                        },
                    },
                    "rotation": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "z": {"type": "number"},
                        },
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "narrate",
            "description": (
                "Send narrative text to the user describing what's happening in the world. "
                "Use this to set the scene, describe events, or respond to the user's imagination. "
                "Keep it evocative but concise."
            ),
            "parameters": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string", "description": "Narrative text to display to the user"},
                },
            },
        },
    },
]

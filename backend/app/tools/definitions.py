"""Tool definitions for the LLM to manipulate the world.

These are OpenAI function calling definitions that allow the LLM to create
3D models via Python code execution, manage the environment, and narrate.
"""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "generate_3d_model",
            "description": (
                "Generate a HYPER-REALISTIC 3D model by writing Python code. This is the ONLY way "
                "to create objects in the scene. You MUST use this tool for every object.\n\n"
                "Available libraries:\n"
                "- `trimesh` - 3D mesh creation, boolean operations, transformations\n"
                "- `np` / `numpy` - numerical operations\n"
                "- `Image`, `ImageDraw`, `ImageFilter` from PIL - texture/skin generation\n"
                "- `scipy` - advanced math operations\n"
                "- `save_model(mesh, name)` - Export as GLB file (MUST call at end)\n\n"
                "## MANDATORY REQUIREMENTS:\n"
                "1. EVERY object MUST have realistic PBR textures generated with PIL. NO plain colors.\n"
                "2. Generate procedural texture images (512x512 minimum) for EVERY surface.\n"
                "3. Apply textures as PBR materials with appropriate roughness and metallic values.\n"
                "4. Build complex objects from MANY parts (10-30+) for detail and realism.\n"
                "5. Use high-subdivision geometry (subdivisions=3-4) for smooth organic surfaces.\n"
                "6. ALWAYS call save_model(mesh, name) at the end.\n\n"
                "## REQUIRED PATTERN - Apply textured skin to every mesh:\n"
                "```python\n"
                "from PIL import Image, ImageDraw, ImageFilter\n"
                "import trimesh\n"
                "import numpy as np\n\n"
                "def make_texture(base_color, detail_func=None, size=512):\n"
                "    '''Create a procedural texture image.'''\n"
                "    img = Image.new('RGB', (size, size), base_color)\n"
                "    draw = ImageDraw.Draw(img)\n"
                "    if detail_func:\n"
                "        detail_func(draw, size)\n"
                "    # Optional: slight blur for realism\n"
                "    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))\n"
                "    return img\n\n"
                "def apply_skin(mesh, texture_img, roughness=0.5, metallic=0.0):\n"
                "    '''Apply a PBR textured skin to a mesh.'''\n"
                "    mat = trimesh.visual.material.PBRMaterial(\n"
                "        baseColorTexture=texture_img,\n"
                "        roughnessFactor=roughness,\n"
                "        metallicFactor=metallic,\n"
                "    )\n"
                "    mesh.visual = trimesh.visual.TextureVisuals(material=mat)\n"
                "```\n\n"
                "## TEXTURE RECIPES (use these as starting points):\n\n"
                "**Wood grain:**\n"
                "```python\n"
                "def wood_detail(draw, s):\n"
                "    for i in range(0, s, 4):\n"
                "        c = tuple(np.clip([130+np.random.randint(-20,20), 80+np.random.randint(-15,15), 35+np.random.randint(-10,10)], 0, 255))\n"
                "        draw.line([(0,i),(s,i+np.random.randint(-3,3))], fill=c, width=np.random.randint(1,3))\n"
                "wood_tex = make_texture((139, 90, 43), wood_detail)\n"
                "```\n\n"
                "**Animal skin/scales:**\n"
                "```python\n"
                "def scale_detail(draw, s):\n"
                "    for _ in range(800):\n"
                "        x, y = np.random.randint(0,s,2)\n"
                "        r = np.random.randint(3,8)\n"
                "        c = tuple(np.clip([60+np.random.randint(-20,20), 120+np.random.randint(-30,30), 40+np.random.randint(-15,15)], 0, 255))\n"
                "        draw.ellipse([x-r,y-r,x+r,y+r], fill=c, outline=(c[0]-20,c[1]-20,c[2]-10))\n"
                "skin_tex = make_texture((70, 130, 50), scale_detail)\n"
                "```\n\n"
                "**Stone/rock:**\n"
                "```python\n"
                "def stone_detail(draw, s):\n"
                "    for _ in range(2000):\n"
                "        x,y = np.random.randint(0,s,2)\n"
                "        v = np.random.randint(100,170)\n"
                "        draw.point((x,y), fill=(v,v-5,v-10))\n"
                "stone_tex = make_texture((140, 138, 132), stone_detail)\n"
                "```\n\n"
                "**Metal:** `metal_tex = make_texture((180,180,190)); apply_skin(mesh, metal_tex, roughness=0.15, metallic=0.9)`\n"
                "**Fabric:** Draw cross-hatch lines with slight color variation\n"
                "**Ceramic:** Solid light color, very low roughness (0.1)\n\n"
                "## GEOMETRY TIPS:\n"
                "- `trimesh.creation.icosphere(subdivisions=3, radius=r)` - smooth spheres\n"
                "- `trimesh.creation.cylinder(radius=r, height=h, sections=32)` - smooth cylinders\n"
                "- `trimesh.creation.box(extents=[w,h,d])` - boxes\n"
                "- `trimesh.creation.cone(radius=r, height=h, sections=32)` - cones\n"
                "- `mesh.apply_translation([x,y,z])` - position parts\n"
                "- `mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))` - rotate\n"
                "- `trimesh.util.concatenate(parts_list)` - combine parts\n"
                "- Vertex manipulation: `mesh.vertices[:, 1] *= 0.5` to flatten\n\n"
                "GOAL: Every model should look like it belongs in a modern 3D game. "
                "Rich textures, proper PBR materials, detailed geometry, realistic proportions."
            ),
            "parameters": {
                "type": "object",
                "required": ["code", "object_name"],
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code using trimesh + PIL to generate the 3D model with textures. Must call save_model() at the end.",
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

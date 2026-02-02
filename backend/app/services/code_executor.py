"""Sandboxed Python code execution for 3D model generation.

Allows the LLM to write Python code that uses trimesh to generate
3D models, which are saved as GLB files and served to the frontend.
"""

from __future__ import annotations

import logging
import os
import tempfile
import traceback
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Directory where generated models are stored
MODELS_DIR = Path(tempfile.gettempdir()) / "dreamscape_models"
MODELS_DIR.mkdir(exist_ok=True)


def execute_model_code(code: str) -> dict[str, Any]:
    """Execute Python code for 3D model generation.

    The code has access to trimesh, numpy, and a special `save_model(mesh, name)`
    function that exports the mesh as GLB and returns the URL.

    Returns a dict with 'success', 'files' (list of generated file info), and 'error'.
    """
    generated_files: list[dict[str, str]] = []

    def save_model(mesh: Any, name: str = "model") -> str:
        """Save a trimesh mesh as GLB and return the relative URL path."""
        file_id = str(uuid.uuid4())[:8]
        filename = f"{name}_{file_id}.glb"
        filepath = MODELS_DIR / filename
        mesh.export(str(filepath), file_type="glb")
        url = f"/models/{filename}"
        generated_files.append({"name": name, "filename": filename, "url": url})
        logger.info("Generated model: %s -> %s", name, filepath)
        return url

    def save_model_stl(mesh: Any, name: str = "model") -> str:
        """Save a trimesh mesh as STL and return the relative URL path."""
        file_id = str(uuid.uuid4())[:8]
        filename = f"{name}_{file_id}.stl"
        filepath = MODELS_DIR / filename
        mesh.export(str(filepath), file_type="stl")
        url = f"/models/{filename}"
        generated_files.append({"name": name, "filename": filename, "url": url})
        logger.info("Generated STL model: %s -> %s", name, filepath)
        return url

    # Build execution namespace with allowed imports
    exec_globals: dict[str, Any] = {
        "__builtins__": __builtins__,
        "save_model": save_model,
        "save_model_stl": save_model_stl,
    }

    logger.info("Executing model code:\n%s", code)

    try:
        import trimesh  # type: ignore[import-untyped]
        import numpy as np

        exec_globals["trimesh"] = trimesh
        exec_globals["np"] = np
        exec_globals["numpy"] = np

        # Make PIL/Pillow available for texture generation
        try:
            from PIL import Image, ImageDraw, ImageFilter  # type: ignore[import-untyped]
            exec_globals["Image"] = Image
            exec_globals["ImageDraw"] = ImageDraw
            exec_globals["ImageFilter"] = ImageFilter
        except ImportError:
            pass

        # Make scipy available for advanced mesh operations
        try:
            import scipy  # type: ignore[import-untyped]
            exec_globals["scipy"] = scipy
        except ImportError:
            pass

        exec(code, exec_globals)  # noqa: S102

        return {
            "success": True,
            "files": generated_files,
            "error": None,
        }

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        logger.error("Code execution failed: %s", error_msg)
        return {
            "success": False,
            "files": generated_files,
            "error": error_msg,
        }


def get_model_path(filename: str) -> Path | None:
    """Get the filesystem path for a generated model file."""
    filepath = MODELS_DIR / filename
    if filepath.exists() and filepath.is_file():
        return filepath
    return None

"""Persistent IPython environment for 3D model generation.

Maintains a long-lived IPython shell so the LLM can define functions,
build on previous code, and reuse variables across executions.
"""

from __future__ import annotations

import logging
import tempfile
import traceback
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Directory where generated models are stored
MODELS_DIR = Path(tempfile.gettempdir()) / "dreamscape_models"
MODELS_DIR.mkdir(exist_ok=True)

# Bootstrap code run once when the IPython shell is created
_BOOTSTRAP_CODE = (
    "import trimesh\n"
    "import numpy as np\n"
    "import numpy\n"
    "from PIL import Image, ImageDraw, ImageFilter\n"
    "\n"
    "try:\n"
    "    import scipy\n"
    "except ImportError:\n"
    "    pass\n"
    "\n"
    "def make_texture(base_color, detail_func=None, size=512):\n"
    "    img = Image.new('RGB', (size, size), base_color)\n"
    "    draw = ImageDraw.Draw(img)\n"
    "    if detail_func:\n"
    "        detail_func(draw, size)\n"
    "    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))\n"
    "    return img\n"
    "\n"
    "def apply_skin(mesh, texture_img, roughness=0.5, metallic=0.0):\n"
    "    mat = trimesh.visual.material.PBRMaterial(\n"
    "        baseColorTexture=texture_img,\n"
    "        roughnessFactor=roughness,\n"
    "        metallicFactor=metallic,\n"
    "    )\n"
    "    mesh.visual = trimesh.visual.TextureVisuals(material=mat)\n"
)


class PersistentExecutor:
    """Wraps an IPython InteractiveShell for persistent code execution."""

    def __init__(self) -> None:
        self._shell: Any = None
        self._generated_files: list[dict[str, str]] = []

    def _ensure_shell(self) -> Any:
        """Lazily create and bootstrap the IPython shell."""
        if self._shell is not None:
            return self._shell

        from IPython.core.interactiveshell import InteractiveShell  # type: ignore[import-untyped]

        self._shell = InteractiveShell.instance()

        # Inject save_model into the shell's namespace
        self._shell.user_ns["save_model"] = self._save_model
        self._shell.user_ns["save_model_stl"] = self._save_model_stl

        # Run bootstrap (imports + helpers)
        result = self._shell.run_cell(_BOOTSTRAP_CODE, silent=True)
        if result.error_in_exec:
            logger.error("Bootstrap failed: %s", result.error_in_exec)

        logger.info("IPython persistent shell initialized")
        return self._shell

    def _save_model(self, mesh: Any, name: str = "model") -> str:
        """Save a trimesh mesh as GLB and return the relative URL path."""
        file_id = str(uuid.uuid4())[:8]
        filename = f"{name}_{file_id}.glb"
        filepath = MODELS_DIR / filename
        mesh.export(str(filepath), file_type="glb")
        url = f"/models/{filename}"
        self._generated_files.append({"name": name, "filename": filename, "url": url})
        logger.info("Generated model: %s -> %s", name, filepath)
        return url

    def _save_model_stl(self, mesh: Any, name: str = "model") -> str:
        """Save a trimesh mesh as STL and return the relative URL path."""
        file_id = str(uuid.uuid4())[:8]
        filename = f"{name}_{file_id}.stl"
        filepath = MODELS_DIR / filename
        mesh.export(str(filepath), file_type="stl")
        url = f"/models/{filename}"
        self._generated_files.append({"name": name, "filename": filename, "url": url})
        logger.info("Generated STL model: %s -> %s", name, filepath)
        return url

    def execute(self, code: str) -> dict[str, Any]:
        """Execute code in the persistent IPython shell.

        Returns a dict with 'success', 'files', and 'error'.
        """
        shell = self._ensure_shell()

        # Reset per-execution file list
        self._generated_files = []

        logger.info("Executing model code:\n%s", code)

        try:
            result = shell.run_cell(code, silent=True)

            if result.error_in_exec:
                error_msg = f"{type(result.error_in_exec).__name__}: {result.error_in_exec}"
                logger.error("Code execution failed: %s", error_msg)
                return {
                    "success": False,
                    "files": self._generated_files,
                    "error": error_msg,
                }

            return {
                "success": True,
                "files": self._generated_files,
                "error": None,
            }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            logger.error("Code execution failed: %s", error_msg)
            return {
                "success": False,
                "files": self._generated_files,
                "error": error_msg,
            }

    def reset(self) -> None:
        """Reset the shell (re-bootstrap on next use)."""
        self._shell = None
        self._generated_files = []
        logger.info("IPython shell reset")


# Module-level singleton
_executor = PersistentExecutor()


def execute_model_code(code: str) -> dict[str, Any]:
    """Execute Python code in the persistent IPython environment."""
    return _executor.execute(code)


def reset_executor() -> None:
    """Reset the persistent executor (e.g. on session reset)."""
    _executor.reset()


def get_model_path(filename: str) -> Path | None:
    """Get the filesystem path for a generated model file."""
    filepath = MODELS_DIR / filename
    if filepath.exists() and filepath.is_file():
        return filepath
    return None

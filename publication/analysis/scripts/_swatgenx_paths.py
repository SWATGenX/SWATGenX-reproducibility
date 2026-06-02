"""Shared, environment-overridable paths to the example SWAT+ model workspaces.

For portability and public release, point these at your own SWATplus_by_VPUID
tree instead of the internal default:

    export SWATGENX_USER_PATH=/path/to/SWATplus/Users
    export SWATGENX_EXAMPLE_USER=admin   # account holding the evaluation models

Scripts import USER_PATH / EXAMPLE_USER / USER_ROOT from here so the internal
deployment path is never hardcoded in more than one place.
"""
from __future__ import annotations

import os
from pathlib import Path

# Root of the per-user SWAT+ workspace tree (default = internal deployment).
USER_PATH = Path(os.environ.get("SWATGENX_USER_PATH", "${SWATGENX_USER_PATH}"))

# Account under USER_PATH that holds the published evaluation models.
EXAMPLE_USER = os.environ.get("SWATGENX_EXAMPLE_USER", "admin")

# Convenience: <USER_PATH>/<EXAMPLE_USER>/SWATplus_by_VPUID
USER_ROOT = USER_PATH / EXAMPLE_USER / "SWATplus_by_VPUID"

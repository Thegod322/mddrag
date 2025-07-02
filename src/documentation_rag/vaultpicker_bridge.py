"""
Bridge to VaultPicker extension for automatic Obsidian vault path detection.
"""
import os
import json
from typing import Optional

def get_current_vault_path() -> Optional[str]:
    """
    Returns the path to the currently active Obsidian vault as set by VaultPicker extension.
    Returns None if not found or file is invalid.
    """
    # Cross-platform path
    if os.name == "nt":
        vault_file = os.path.expandvars(r"%USERPROFILE%\.vaultpicker\active_vault.json")
    else:
        vault_file = os.path.expanduser("~/.vaultpicker/active_vault.json")
    if os.path.exists(vault_file):
        try:
            with open(vault_file, encoding="utf-8") as f:
                vault = json.load(f)
                return vault.get("path")
        except Exception:
            return None
    return None

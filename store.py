"""Local profile store.

The CH57x macropad is write-only: it cannot report back what is stored on each
key (confirmed empirically — no feature reports, no query responds). So, exactly
like the original Windows tool, we remember what *we* programmed. Every binding
sent through this app is recorded here per layer, and the "view" feature reads
it back.

Limitation: this only reflects bindings made with THIS tool. Anything programmed
by the original .exe or another tool is unknown to us.
"""
from __future__ import annotations
import json
import os
import sys

LAYERS = (1, 2, 3)


def _data_dir() -> str:
    # Keep the profile in a stable, writable place (not inside the PyInstaller
    # temp extraction dir).
    base = os.environ.get("APPDATA")
    if not base:
        base = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                else os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(base, "MiniKeyboard")
    return d


PROFILE_PATH = os.path.join(_data_dir(), "profile.json")


class Profile:
    def __init__(self, layers: dict | None = None, path: str = PROFILE_PATH):
        self.path = path
        # layers: { "1": {target: spec}, ... } ; spec is whatever the user passed
        self.layers: dict[str, dict] = {str(n): {} for n in LAYERS}
        if layers:
            for k, v in layers.items():
                self.layers[str(k)] = dict(v)

    @classmethod
    def load(cls, path: str = PROFILE_PATH) -> "Profile":
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            return cls(raw.get("layers", {}), path)
        except (FileNotFoundError, ValueError):
            return cls(path=path)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"device": "1189:8890", "layers": self.layers}, f, indent=2)

    def set(self, layer: int, target: str, spec):
        self.layers.setdefault(str(layer), {})[target.upper()] = spec

    def clear(self, layer: int, target: str):
        self.layers.get(str(layer), {}).pop(target.upper(), None)

    def get(self, layer: int, target: str):
        return self.layers.get(str(layer), {}).get(target.upper())

    def get_layer(self, layer: int) -> dict:
        return dict(self.layers.get(str(layer), {}))

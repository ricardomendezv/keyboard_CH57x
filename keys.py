"""Key/usage tables and human-friendly action parsing for the CH57x macropad.

Everything here is pure data + parsing (no USB). The protocol module turns the
`Press` / `Media` / `Mouse` objects produced here into device bytes.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# HID modifier bits (left side). Right-side variants are +0x10 but rarely used.
# ---------------------------------------------------------------------------
MODIFIERS = {
    "ctrl": 0x01, "control": 0x01,
    "shift": 0x02,
    "alt": 0x04, "option": 0x04,
    "win": 0x08, "gui": 0x08, "cmd": 0x08, "super": 0x08, "meta": 0x08,
}

# ---------------------------------------------------------------------------
# HID keyboard usage codes (Usage Page 0x07). Names are lower-case.
# ---------------------------------------------------------------------------
HID_KEYS: dict[str, int] = {}
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    HID_KEYS[c] = 0x04 + i
for i, c in enumerate("1234567890"):
    HID_KEYS[c] = 0x1E + i
HID_KEYS.update({
    "enter": 0x28, "return": 0x28, "esc": 0x29, "escape": 0x29,
    "backspace": 0x2A, "bksp": 0x2A, "tab": 0x2B, "space": 0x2C, "spacebar": 0x2C,
    "minus": 0x2D, "-": 0x2D, "equal": 0x2E, "=": 0x2E,
    "lbracket": 0x2F, "[": 0x2F, "rbracket": 0x30, "]": 0x30,
    "backslash": 0x31, "\\": 0x31, "semicolon": 0x33, ";": 0x33,
    "quote": 0x34, "'": 0x34, "grave": 0x35, "`": 0x35,
    "comma": 0x36, ",": 0x36, "period": 0x37, ".": 0x37, "slash": 0x38, "/": 0x38,
    "capslock": 0x39,
    "f1": 0x3A, "f2": 0x3B, "f3": 0x3C, "f4": 0x3D, "f5": 0x3E, "f6": 0x3F,
    "f7": 0x40, "f8": 0x41, "f9": 0x42, "f10": 0x43, "f11": 0x44, "f12": 0x45,
    "printscreen": 0x46, "prtsc": 0x46, "scrolllock": 0x47, "pause": 0x48,
    "insert": 0x49, "ins": 0x49, "home": 0x4A, "pageup": 0x4B, "pgup": 0x4B,
    "delete": 0x4C, "del": 0x4C, "end": 0x4D, "pagedown": 0x4E, "pgdn": 0x4E,
    "right": 0x4F, "left": 0x50, "down": 0x51, "up": 0x52,
})

# ---------------------------------------------------------------------------
# Consumer / multimedia usage codes (Usage Page 0x0C), 16-bit.
# ---------------------------------------------------------------------------
MEDIA: dict[str, int] = {
    "play_pause": 0xCD, "playpause": 0xCD, "play": 0xCD,
    "next": 0xB5, "next_track": 0xB5, "prev": 0xB6, "previous": 0xB6, "prev_track": 0xB6,
    "stop": 0xB7, "fast_forward": 0xB3, "rewind": 0xB4,
    "mute": 0xE2, "volume_up": 0xE9, "vol_up": 0xE9, "volume_down": 0xEA, "vol_down": 0xEA,
    "eject": 0xB8,
    "browser": 0x196, "browser_home": 0x223, "browser_back": 0x224, "browser_forward": 0x225,
    "search": 0x221, "email": 0x18A, "mail": 0x18A, "calculator": 0x192, "calc": 0x192,
    "explorer": 0x194, "media_player": 0x183, "screen_lock": 0x19E,
    "brightness_up": 0x6F, "brightness_down": 0x70,
}

# ---------------------------------------------------------------------------
# Mouse button mask bits.
# ---------------------------------------------------------------------------
MOUSE_BUTTONS = {"left": 0x01, "right": 0x02, "middle": 0x04}


# ---------------------------------------------------------------------------
# Action value objects (produced by parsing, consumed by protocol.py)
# ---------------------------------------------------------------------------
@dataclass
class Press:
    """One keyboard chord: modifier bits + a single HID usage code."""
    modifier: int = 0
    code: int = 0


@dataclass
class KeyAction:
    """Keyboard macro: a sequence of up to 5 chords (the device limit)."""
    presses: list[Press] = field(default_factory=list)
    kind: str = "key"


@dataclass
class MediaAction:
    code: int = 0
    kind: str = "media"


@dataclass
class MouseAction:
    buttons: int = 0
    dx: int = 0
    dy: int = 0
    wheel: int = 0
    modifier: int = 0
    kind: str = "mouse"


MAX_PRESSES = 5  # hardware limit per key


# ---------------------------------------------------------------------------
# Ready-made "work" shortcuts. Values are combo strings parsed below.
# ---------------------------------------------------------------------------
SHORTCUTS: dict[str, str] = {
    "copy": "ctrl+c", "paste": "ctrl+v", "cut": "ctrl+x",
    "undo": "ctrl+z", "redo": "ctrl+y",
    "select_all": "ctrl+a", "save": "ctrl+s", "save_as": "ctrl+shift+s",
    "open": "ctrl+o", "new": "ctrl+n", "print": "ctrl+p",
    "find": "ctrl+f", "find_replace": "ctrl+h",
    "bold": "ctrl+b", "italic": "ctrl+i", "underline": "ctrl+u",
    "zoom_in": "ctrl+=", "zoom_out": "ctrl+-",
    "close_tab": "ctrl+w", "reopen_tab": "ctrl+shift+t", "new_tab": "ctrl+t",
    "switch_app": "alt+tab", "show_desktop": "win+d", "lock": "win+l",
    "task_view": "win+tab", "screenshot": "win+shift+s",
    "close_window": "alt+f4", "task_manager": "ctrl+shift+esc",
    "comment_code": "ctrl+/", "delete_line": "ctrl+shift+k",
    "next_word": "ctrl+right", "prev_word": "ctrl+left",
}


class ParseError(ValueError):
    pass


def parse_chord(text: str) -> Press:
    """'ctrl+shift+t' -> Press(modifier, code). A single character is allowed,
    e.g. 'A' becomes shift+a automatically (so the key types an upper-case A)."""
    text = text.strip()
    if not text:
        raise ParseError("empty key")
    # A lone uppercase ASCII letter/symbol -> auto add shift.
    if len(text) == 1 and text.isupper():
        return Press(MODIFIERS["shift"], HID_KEYS[text.lower()])
    parts = [p.strip().lower() for p in text.split("+") if p.strip()]
    mod = 0
    code = 0
    for p in parts:
        if p in MODIFIERS:
            mod |= MODIFIERS[p]
        elif p in HID_KEYS:
            if code:
                raise ParseError(f"more than one non-modifier key in '{text}'")
            code = HID_KEYS[p]
        else:
            raise ParseError(f"unknown key '{p}' in '{text}'")
    if not code and not mod:
        raise ParseError(f"nothing to bind in '{text}'")
    return Press(mod, code)


def make_key_action(spec) -> KeyAction:
    """Build a keyboard macro (<=5 chords).

    Accepts:
      - a shortcut name found in SHORTCUTS  ('copy')
      - a single chord string               ('ctrl+shift+t')
      - a list of chord strings (sequence)  (['h','e','l','l','o'])
      - a plain word to type out            ('hello')  -> one chord per letter
    """
    if isinstance(spec, str) and spec in SHORTCUTS:
        spec = SHORTCUTS[spec]
    if isinstance(spec, list):
        chords = [parse_chord(s) for s in spec]
    elif isinstance(spec, str) and "+" not in spec and len(spec) > 1 and spec not in HID_KEYS:
        # treat as text to type, one chord per character
        chords = [parse_chord(ch) for ch in spec]
    else:
        chords = [parse_chord(spec)]
    if len(chords) > MAX_PRESSES:
        raise ParseError(f"max {MAX_PRESSES} key presses per key (got {len(chords)})")
    return KeyAction(presses=chords)


def make_media_action(name: str) -> MediaAction:
    key = name.strip().lower()
    if key not in MEDIA:
        raise ParseError(f"unknown media key '{name}'. Options: {', '.join(sorted(MEDIA))}")
    return MediaAction(code=MEDIA[key])


def parse_action(spec):
    """Top-level dispatcher used by the CLI and GUI.

    spec may be a dict ({'media': 'volume_up'}, {'mouse': {...}}, {'keys': [...]},
    {'key': 'ctrl+c'}) or a string. Bare strings are keyboard actions; the
    prefixes 'media:', 'mouse:' and 'key:' select the type explicitly.
    """
    if isinstance(spec, dict):
        if "media" in spec:
            return make_media_action(spec["media"])
        if "mouse" in spec:
            return make_mouse_action(spec["mouse"])
        if "keys" in spec:
            return make_key_action(spec["keys"])
        if "key" in spec:
            return make_key_action(spec["key"])
        raise ParseError(f"binding dict needs one of media/mouse/keys/key: {spec!r}")
    s = str(spec).strip()
    if s.lower().startswith("media:"):
        return make_media_action(s[6:])
    if s.lower().startswith("mouse:"):
        return make_mouse_action(s[6:])
    if s.lower().startswith("key:"):
        return make_key_action(s[4:])
    return make_key_action(s)


def make_mouse_action(spec: dict | str) -> MouseAction:
    """spec examples:
        'left_click' / 'right_click' / 'middle_click'
        'wheel_up' / 'wheel_down'
        {'click': 'left'} / {'wheel': 1} / {'move': [10, -5]} / {'drag': 'left', 'move': [5, 10]}
    """
    if isinstance(spec, str):
        s = spec.strip().lower()
        presets = {
            "left_click": {"click": "left"}, "right_click": {"click": "right"},
            "middle_click": {"click": "middle"},
            "wheel_up": {"wheel": 1}, "wheel_down": {"wheel": -1},
        }
        if s not in presets:
            raise ParseError(f"unknown mouse action '{spec}'")
        spec = presets[s]
    act = MouseAction()
    if "click" in spec or "drag" in spec:
        btn = (spec.get("click") or spec.get("drag")).lower()
        if btn not in MOUSE_BUTTONS:
            raise ParseError(f"unknown mouse button '{btn}'")
        act.buttons = MOUSE_BUTTONS[btn]
    if "move" in spec:
        act.dx, act.dy = int(spec["move"][0]), int(spec["move"][1])
    if "wheel" in spec:
        act.wheel = int(spec["wheel"])
    if "mod" in spec or "modifier" in spec:
        for p in str(spec.get("mod") or spec.get("modifier")).lower().split("+"):
            act.modifier |= MODIFIERS.get(p.strip(), 0)
    return act

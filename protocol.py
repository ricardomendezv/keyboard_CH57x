"""USB-HID wire protocol for the CH57x macropad (VID 0x1189 / PID 0x8890).

Byte layout verified two independent ways: decoded from the original
MINI KeyBoard.exe and against kriomant/ch57x-keyboard-tool's test vectors.
See memory note `ch57x-8890-protocol` for the full spec.
"""
from __future__ import annotations
import re
import time

import hid

from keys import KeyAction, MediaAction, MouseAction

VID = 0x1189
PID = 0x8890
CONFIG_INTERFACE = 1          # MI_01, the vendor-defined config interface
CONFIG_USAGE_PAGE = 0xFF00
REPORT_LEN = 65               # report id (0x03) + 64 data bytes
REPORT_ID = 0x03
MAX_LAYER = 3                 # device supports 3 layers


# ---------------------------------------------------------------------------
# Target (key/knob) addressing
# ---------------------------------------------------------------------------
def to_key_id(target: str) -> int:
    """'KEY1'..'KEY12' -> 1..12.  Knobs 'K1L/K1P/K1R'.. -> 13..21
    (L=rotate left/CCW, P=press, R=rotate right/CW)."""
    t = target.strip().upper().replace(" ", "")
    m = re.fullmatch(r"KEY(\d{1,2})", t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 12:
            return n
    m = re.fullmatch(r"K(?:NOB)?([123])([LPR])", t)
    if m:
        n = int(m.group(1))
        action = {"L": 0, "P": 1, "R": 2}[m.group(2)]
        return 13 + 3 * (n - 1) + action
    raise ValueError(f"unknown target '{target}' (use KEY1..KEY12 or K1L/K1P/K1R..K3R)")


ALL_TARGETS = (
    [f"KEY{i}" for i in range(1, 13)]
    + [f"K{n}{a}" for n in (1, 2, 3) for a in ("L", "P", "R")]
)


# ---------------------------------------------------------------------------
# Message encoders -> each returns a list of message byte-lists.
# The report id 0x03 is the first byte of every message.
# ---------------------------------------------------------------------------
def _s8(v: int) -> int:
    """signed int8 -> unsigned byte (two's complement)."""
    v = max(-128, min(127, int(v)))
    return v & 0xFF


def start_message(layer: int) -> list[int]:
    return [REPORT_ID, 0xFE, layer + 1, 0x01, 0x01]


FINISH_MESSAGE = [REPORT_ID, 0xAA, 0xAA]


def encode(key_id: int, layer: int, action) -> list[list[int]]:
    """Return the payload messages (without start/finish) for one binding."""
    if isinstance(action, KeyAction):
        type_byte = ((layer + 1) << 4) | 0x01
        count = len(action.presses)
        msgs = [[REPORT_ID, key_id, type_byte, count]]            # header
        for i, pr in enumerate(action.presses, start=1):
            msgs.append([REPORT_ID, key_id, type_byte, count, i, pr.modifier & 0xFF, pr.code & 0xFF])
        return msgs
    if isinstance(action, MediaAction):
        type_byte = ((layer + 1) << 4) | 0x02
        return [[REPORT_ID, key_id, type_byte, action.code & 0xFF, (action.code >> 8) & 0xFF]]
    if isinstance(action, MouseAction):
        type_byte = ((layer + 1) << 4) | 0x03
        return [[REPORT_ID, key_id, type_byte, action.buttons & 0xFF,
                 _s8(action.dx), _s8(action.dy), _s8(action.wheel), action.modifier & 0xFF]]
    raise TypeError(f"unsupported action {action!r}")


def build_binding(target: str, layer: int, action) -> list[list[int]]:
    """Full wire sequence (start + payload + finish) to program one key."""
    if not (0 <= layer < MAX_LAYER):
        raise ValueError(f"layer must be 0..{MAX_LAYER - 1}")
    key_id = to_key_id(target)
    return [start_message(layer), *encode(key_id, layer, action), FINISH_MESSAGE]


def _pad(msg: list[int]) -> bytes:
    if len(msg) > REPORT_LEN:
        raise ValueError("message too long")
    return bytes(msg) + bytes(REPORT_LEN - len(msg))


def hexdump(msgs: list[list[int]]) -> str:
    return "\n".join(" ".join(f"{b:02X}" for b in m) for m in msgs)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------
class DeviceNotFound(Exception):
    pass


class Keypad:
    """Open the macropad's config interface and program keys."""

    def __init__(self, delay: float = 0.003):
        self.delay = delay
        self._dev = None
        self.path = None

    @staticmethod
    def find_path() -> bytes | None:
        for d in hid.enumerate(VID, PID):
            if d.get("interface_number") == CONFIG_INTERFACE and d["usage_page"] == CONFIG_USAGE_PAGE:
                return d["path"]
        # fallback: any FF00 collection
        for d in hid.enumerate(VID, PID):
            if d["usage_page"] == CONFIG_USAGE_PAGE:
                return d["path"]
        return None

    @staticmethod
    def is_connected() -> bool:
        return Keypad.find_path() is not None

    def open(self):
        path = self.find_path()
        if not path:
            raise DeviceNotFound(
                "CH57x macropad (1189:8890) config interface not found. Is it plugged in?"
            )
        # Two competing packages expose 'hid': the cython 'hidapi' package gives
        # hid.device()+open_path(); the pure-python 'hid' package gives hid.Device(path=).
        if hasattr(hid, "Device"):
            self._dev = hid.Device(path=path)
        else:
            dev = hid.device()
            dev.open_path(path)
            self._dev = dev
        self.path = path
        return self

    def close(self):
        if self._dev:
            try:
                self._dev.close()
            except Exception:
                pass
            self._dev = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *exc):
        self.close()

    def _send(self, msg: list[int]):
        buf = _pad(msg)
        # cython hidapi's write() wants a list of ints; the 'hid' package takes bytes.
        n = self._dev.write(list(buf) if not hasattr(hid, "Device") else buf)
        if n is not None and n < 0:
            raise IOError(f"HID write failed for message {msg}")
        if self.delay:
            time.sleep(self.delay)

    def program(self, target: str, layer: int, action) -> list[list[int]]:
        """Program one key/knob. Returns the messages sent (for logging)."""
        msgs = build_binding(target, layer, action)
        for m in msgs:
            self._send(m)
        return msgs

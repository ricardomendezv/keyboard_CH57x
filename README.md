# Mini Keyboard — Python edition (CH57x 12-key + knobs)

A clean, scriptable replacement for the original *MINI KeyBoard* Windows tool, for the
macropad with USB id **VID 0x1189 / PID 0x8890** (CH57x chip). No on-screen keyboard:
you assign each key/knob by name or by typing any keyboard combo.

It supports **keyboard keys & combos, work shortcuts (copy/paste/cut/undo/redo/save…),
multimedia keys, and mouse actions (clicks, wheel, move)**. Each key holds up to **5**
key-presses (a hardware limit).

## Windows Download
[MiniKeyboard.exe](https://github.com/ricardomendezv/keyboard_CH57x/tree/main/dist/MiniKeyboard.exe)

## Install requirements

```powershell
cd "C:\Users\M3X\Documents\GitHub\MINI KEYBOARD TOOL V1\python"
pip install -r requirements.txt
```

## GUI

```powershell
python gui.py
```

For every key (KEY1–KEY12) and knob action (Knob1/2 left·press·right) pick a preset from
the dropdown or type any combo (e.g. `ctrl+shift+t`). Choose the **Layer** (1–3),
hit **Program** on a row or **Program ALL**. **Preview bytes** shows exactly what would be
sent without writing.

## Command line

```powershell
python cli.py status                         # is the macropad connected?
python cli.py list                           # all shortcut / media / mouse names
python cli.py set KEY1 copy                  # KEY1 -> Ctrl+C  (layer 1)
python cli.py set K1R media:volume_up        # knob1 turn-right -> volume up
python cli.py set KEY5 mouse:left_click
python cli.py set KEY9 "ctrl+shift+t" --layer 2
python cli.py apply config.example.json          # program everything from a file
python cli.py apply config.example.json --dry-run  # show bytes, write nothing
```

## Config file format

```json
{
  "layer": 1,
  "bindings": [
    { "target": "KEY1", "action": "copy" },
    { "target": "KEY2", "action": "ctrl+shift+t" },
    { "target": "K1R",  "action": { "media": "volume_up" } },
    { "target": "K2P",  "action": { "mouse": "left_click" } },
    { "target": "KEY3", "action": { "keys": ["h", "e", "l", "l", "o"] } }
  ]
}
```

**Targets:** `KEY1`–`KEY12`; knobs `K1L/K1P/K1R`, `K2L/K2P/K2R` (and `K3*` if present)
— L = rotate left, P = press, R = rotate right.

**Action forms:**
- a shortcut name: `copy paste cut undo redo save select_all find …` (see `python cli.py list`)
- any combo string: `ctrl+alt+del`, `win+shift+s`, `f5`, a single key `a`, or `A` (= Shift+A)
- `media:NAME` — `volume_up volume_down mute play_pause next prev stop …`
- `mouse:NAME` — `left_click right_click middle_click wheel_up wheel_down`
- JSON `{ "mouse": { "wheel": 1 } }` / `{ "mouse": { "drag": "left", "move": [5, 10] } }`
- JSON `{ "keys": [ ... up to 5 ... ] }` for a multi-key macro

## How it works / verifying

`python selftest.py` checks the byte encoder against the device's known reference vectors
(no hardware needed). The wire protocol is documented inline in `protocol.py`.

| file | purpose |
|------|---------|
| `protocol.py` | device discovery + HID byte encoder + send sequence |
| `keys.py` | HID tables, shortcut/media/mouse presets, parsing |
| `cli.py` | command-line interface |
| `gui.py` | tkinter GUI |
| `selftest.py` | offline protocol verification |

> Writing is done only on **Program / apply** (not on preview). Bindings are layered, so
> reprogramming a key just overwrites it — nothing is permanent.

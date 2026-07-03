# CH57x Macropad — User Manual

## Table of Contents

- [CLI Commands](#cli-commands)
- [Targets (keys & knobs)](#targets-keys--knobs)
- [Action Types](#action-types)
  - [Work Shortcuts](#work-shortcuts)
  - [Key Combos](#key-combos)
  - [Media Keys](#media-keys)
  - [Mouse Actions](#mouse-actions)
  - [Multi-key Macros](#multi-key-macros)
- [Config File](#config-file)
- [Layers](#layers)
- [GUI](#gui)

---

## CLI Commands

```
python cli.py <command> [options]
```

| Command | What it does |
|---------|-------------|
| `status` | Check if the macropad is connected |
| `list` | Print all valid shortcut / media / mouse names |
| `set <target> <action>` | Program one key or knob |
| `apply <config.json>` | Program everything from a JSON file |
| `view` | Show what this tool has stored per key per layer |

### `status`
```powershell
python cli.py status
```
Prints `Connected` or `NOT connected`.

### `list`
```powershell
python cli.py list
```
Prints all named shortcuts, media keys, mouse actions, and valid targets.

### `set`
```powershell
python cli.py set <target> <action> [--layer 1|2|3] [--dry-run]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--layer` | `1` | Which layer (1–3) to write |
| `--dry-run` | off | Print the bytes that would be sent without writing |

Examples:
```powershell
python cli.py set KEY1 copy                    # Ctrl+C on layer 1
python cli.py set KEY9 "ctrl+shift+t"          # reopen tab
python cli.py set K1R media:volume_up          # knob1 right = volume up
python cli.py set KEY5 mouse:left_click
python cli.py set KEY3 "ctrl+shift+t" --layer 2
python cli.py set KEY1 copy --dry-run          # preview bytes only
```

### `apply`
```powershell
python cli.py apply config.json [--dry-run]
```
Programs every binding in the JSON file in one shot. `--dry-run` shows the bytes without writing.

### `view`
```powershell
python cli.py view [--layer 1|2|3]
```
Shows the stored bindings from the last `set` / `apply` calls. Omit `--layer` to see all three layers.

---

## Targets (keys & knobs)

| Target | Physical location |
|--------|-----------------|
| `KEY1` – `KEY12` | The 12 push keys |
| `K1L` | Knob 1 rotate left |
| `K1P` | Knob 1 press |
| `K1R` | Knob 1 rotate right |
| `K2L` | Knob 2 rotate left |
| `K2P` | Knob 2 press |
| `K2R` | Knob 2 rotate right |
| `K3L/K3P/K3R` | Knob 3 (if present) |

---

## Action Types

### Work Shortcuts

Use the name directly — no prefix needed.

| Name | Sends |
|------|-------|
| `copy` | Ctrl+C |
| `paste` | Ctrl+V |
| `cut` | Ctrl+X |
| `undo` | Ctrl+Z |
| `redo` | Ctrl+Y |
| `save` | Ctrl+S |
| `save_as` | Ctrl+Shift+S |
| `select_all` | Ctrl+A |
| `open` | Ctrl+O |
| `new` | Ctrl+N |
| `print` | Ctrl+P |
| `find` | Ctrl+F |
| `find_replace` | Ctrl+H |
| `bold` | Ctrl+B |
| `italic` | Ctrl+I |
| `underline` | Ctrl+U |
| `zoom_in` | Ctrl+= |
| `zoom_out` | Ctrl+- |
| `close_tab` | Ctrl+W |
| `reopen_tab` | Ctrl+Shift+T |
| `new_tab` | Ctrl+T |
| `switch_app` | Alt+Tab |
| `show_desktop` | Win+D |
| `lock` | Win+L |
| `task_view` | Win+Tab |
| `screenshot` | Win+Shift+S |
| `close_window` | Alt+F4 |
| `task_manager` | Ctrl+Shift+Esc |
| `comment_code` | Ctrl+/ |
| `delete_line` | Ctrl+Shift+K |
| `next_word` | Ctrl+Right |
| `prev_word` | Ctrl+Left |

Run `python cli.py list` to always get the current list.

### Key Combos

Any `modifier+key` string works. Modifiers can be combined with `+`.

**Modifiers:** `ctrl`, `shift`, `alt`, `win` (also: `control`, `option`, `gui`, `cmd`, `super`, `meta`)

**Keys:** `a`–`z`, `0`–`9`, `f1`–`f12`, and:

| Name(s) | Key |
|---------|-----|
| `enter`, `return` | Enter |
| `esc`, `escape` | Escape |
| `backspace`, `bksp` | Backspace |
| `tab` | Tab |
| `space`, `spacebar` | Space |
| `up`, `down`, `left`, `right` | Arrow keys |
| `home`, `end` | Home / End |
| `pageup`, `pgup` | Page Up |
| `pagedown`, `pgdn` | Page Down |
| `insert`, `ins` | Insert |
| `delete`, `del` | Delete |
| `capslock` | Caps Lock |
| `printscreen`, `prtsc` | Print Screen |
| `scrolllock` | Scroll Lock |
| `pause` | Pause |
| `-`, `minus` | - |
| `=`, `equal` | = |
| `[`, `lbracket` | [ |
| `]`, `rbracket` | ] |
| `\`, `backslash` | \ |
| `;`, `semicolon` | ; |
| `'`, `quote` | ' |
| `` ` ``, `grave` | ` |
| `,`, `comma` | , |
| `.`, `period` | . |
| `/`, `slash` | / |

Examples:
```
ctrl+c
ctrl+shift+t
win+shift+s
alt+f4
f5
```

A lone uppercase letter like `A` automatically becomes `shift+a` (types capital A).

### Media Keys

Prefix with `media:` on the CLI, or use `{ "media": "name" }` in JSON.

| Name(s) | Action |
|---------|--------|
| `play_pause`, `playpause`, `play` | Play / Pause |
| `next`, `next_track` | Next track |
| `prev`, `previous`, `prev_track` | Previous track |
| `stop` | Stop |
| `fast_forward` | Fast forward |
| `rewind` | Rewind |
| `mute` | Mute |
| `volume_up`, `vol_up` | Volume up |
| `volume_down`, `vol_down` | Volume down |
| `eject` | Eject |
| `browser` | Open browser |
| `browser_home` | Browser home |
| `browser_back` | Browser back |
| `browser_forward` | Browser forward |
| `search` | Search |
| `email`, `mail` | Open email client |
| `calculator`, `calc` | Open calculator |
| `explorer` | File Explorer |
| `media_player` | Media player |
| `screen_lock` | Lock screen |
| `brightness_up` | Brightness up |
| `brightness_down` | Brightness down |

CLI: `python cli.py set K1R media:volume_up`  
JSON: `{ "media": "volume_up" }`

### Mouse Actions

Prefix with `mouse:` on the CLI, or use `{ "mouse": "name" }` / `{ "mouse": {...} }` in JSON.

**Presets (string form):**

| Name | Action |
|------|--------|
| `left_click` | Left mouse button click |
| `right_click` | Right mouse button click |
| `middle_click` | Middle mouse button click |
| `wheel_up` | Scroll wheel up |
| `wheel_down` | Scroll wheel down |

CLI: `python cli.py set KEY5 mouse:left_click`  
JSON: `{ "mouse": "left_click" }`

**Advanced (dict form — JSON only):**

```json
{ "mouse": { "click": "left" } }
{ "mouse": { "click": "right" } }
{ "mouse": { "click": "middle" } }
{ "mouse": { "wheel": 1 } }          // scroll up
{ "mouse": { "wheel": -1 } }         // scroll down
{ "mouse": { "move": [10, -5] } }    // move cursor dx=10, dy=-5
{ "mouse": { "drag": "left", "move": [5, 10] } }  // left-drag + move
```

You can add a `"mod"` key to hold a modifier during the action:
```json
{ "mouse": { "click": "left", "mod": "ctrl" } }
```

### Multi-key Macros

Send up to **5** key presses in sequence (hardware limit).

JSON:
```json
{ "keys": ["ctrl+c", "ctrl+v"] }
{ "keys": ["h", "e", "l", "l", "o"] }
```

A plain multi-character string with no `+` is also typed letter by letter:
```powershell
python cli.py set KEY1 hello    # types h-e-l-l-o (5 presses)
```

---

## Config File

Program multiple keys at once with a JSON file.

```json
{
  "layer": 1,
  "bindings": [
    { "target": "KEY1",  "action": "copy" },
    { "target": "KEY2",  "action": "paste" },
    { "target": "KEY9",  "action": "ctrl+shift+t" },
    { "target": "KEY10", "action": "win+shift+s" },
    { "target": "KEY11", "action": { "media": "play_pause" } },
    { "target": "KEY12", "action": { "mouse": "middle_click" } },
    { "target": "K1L",   "action": { "media": "volume_down" } },
    { "target": "K1P",   "action": { "media": "mute" } },
    { "target": "K1R",   "action": { "media": "volume_up" } },
    { "target": "K2L",   "action": { "mouse": { "wheel": -1 } } },
    { "target": "K2P",   "action": { "mouse": "left_click" } },
    { "target": "K2R",   "action": { "mouse": { "wheel": 1 } } }
  ]
}
```

Each binding can override the top-level `layer` with its own `"layer"` field:
```json
{ "target": "KEY3", "layer": 2, "action": "save_as" }
```

Apply it:
```powershell
python cli.py apply config.json
python cli.py apply config.json --dry-run   # preview only
```

See `config.example.json` for a ready-to-use starter.

---

## Layers

The macropad supports **3 layers**. Only one layer is active at a time (switched on the device). Each layer has independent bindings for all keys and knobs.

Specify a layer with `--layer` on the CLI, or with `"layer"` in the config file (defaults to `1`).

---

## GUI

```powershell
python gui.py
```

- Select a **Layer** (1–3) at the top.
- For each key / knob row, pick a preset from the dropdown or type any action string (e.g. `ctrl+shift+t`, `media:volume_up`).
- **Program** writes a single row to the device.
- **Program ALL** writes every row at once.
- **Preview bytes** shows the raw HID bytes without writing anything.

---

## Verifying / Testing

```powershell
python selftest.py
```

Runs the byte encoder against known reference vectors — no hardware required. Useful to check that a change to `protocol.py` or `keys.py` didn't break encoding.

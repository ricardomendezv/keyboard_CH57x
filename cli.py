"""Command-line control for the CH57x macropad.

Examples:
  python cli.py status
  python cli.py set KEY1 copy                 # bind KEY1 (layer 1) to Ctrl+C
  python cli.py set K1L media:volume_down     # knob1 rotate-left -> volume down
  python cli.py set KEY5 "mouse:left_click"
  python cli.py set KEY3 "ctrl+shift+t" --layer 2
  python cli.py apply config.json
  python cli.py apply config.json --dry-run    # show bytes, don't write
  python cli.py list                           # show available shortcuts/media
"""
from __future__ import annotations
import argparse
import json
import sys

import keys
from keys import SHORTCUTS, MEDIA, MOUSE_BUTTONS, parse_action
from protocol import Keypad, DeviceNotFound, build_binding, hexdump, ALL_TARGETS, to_key_id
from store import Profile, LAYERS


def _spec_str(spec) -> str:
    return spec if isinstance(spec, str) else json.dumps(spec)


def cmd_status(_args):
    path = Keypad.find_path()
    if path:
        print("Connected: CH57x macropad (1189:8890) config interface found.")
        print("  path:", path.decode(errors="replace"))
    else:
        print("NOT connected: plug in the macropad (VID 1189 / PID 8890).")
        return 1
    return 0


def cmd_list(_args):
    print("Work shortcuts (use the name directly):")
    for k in sorted(SHORTCUTS):
        print(f"  {k:<14} = {SHORTCUTS[k]}")
    print("\nMultimedia (use as  media:NAME ):")
    print("  " + ", ".join(sorted(MEDIA)))
    print("\nMouse (use as  mouse:NAME  or mouse:{...} in JSON):")
    print("  left_click, right_click, middle_click, wheel_up, wheel_down")
    print("  buttons:", ", ".join(MOUSE_BUTTONS))
    print("\nTargets:")
    print("  " + ", ".join(ALL_TARGETS))
    print("\nAny keyboard combo also works, e.g.  ctrl+alt+del , win+shift+s , f5")
    return 0


def _program(bindings, dry_run: bool):
    """bindings: list of (target, layer, action). layer is 0-based here."""
    if dry_run:
        for target, layer, action in bindings:
            print(f"# {target} (layer {layer + 1})")
            print(hexdump(build_binding(target, layer, action)))
            print()
        print("(dry-run: nothing written to the device)")
        return 0
    try:
        with Keypad() as kp:
            for target, layer, action in bindings:
                kp.program(target, layer, action)
                print(f"programmed {target} (layer {layer + 1})")
    except DeviceNotFound as e:
        print("ERROR:", e, file=sys.stderr)
        return 1
    print("Done.")
    return 0


def cmd_set(args):
    layer = args.layer - 1
    action = parse_action(args.action)
    to_key_id(args.target)  # validate early
    rc = _program([(args.target, layer, action)], args.dry_run)
    if rc == 0 and not args.dry_run:
        prof = Profile.load()
        prof.set(args.layer, args.target, args.action)
        prof.save()
    return rc


def cmd_apply(args):
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    default_layer = cfg.get("layer", 1)
    bindings = []
    specs = []
    for b in cfg.get("bindings", []):
        target = b["target"]
        layer1 = b.get("layer", default_layer)
        spec = b.get("action", b)
        bindings.append((target, layer1 - 1, parse_action(spec)))
        specs.append((layer1, target, spec))
    if not bindings:
        print("No bindings found in config.", file=sys.stderr)
        return 1
    rc = _program(bindings, args.dry_run)
    if rc == 0 and not args.dry_run:
        prof = Profile.load()
        for layer1, target, spec in specs:
            prof.set(layer1, target, spec)
        prof.save()
    return rc


def cmd_view(args):
    prof = Profile.load()
    layers = [args.layer] if args.layer else LAYERS
    print(f"(stored bindings - what this tool has programmed; file: {prof.path})")
    for L in layers:
        data = prof.get_layer(L)
        print(f"\n== Layer {L} ==")
        for t in ALL_TARGETS:
            spec = data.get(t)
            shown = _spec_str(spec) if spec is not None else "-"
            print(f"  {t:<6} {shown}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="CH57x macropad control (Python).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("status", help="check connection")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("list", help="list shortcuts / media / mouse names")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("set", help="program one key/knob")
    sp.add_argument("target", help="KEY1..KEY12 or K1L/K1P/K1R..K3R")
    sp.add_argument("action", help="shortcut name, combo, media:NAME, or mouse:NAME")
    sp.add_argument("--layer", type=int, default=1, choices=(1, 2, 3))
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("apply", help="program everything from a JSON config")
    sp.add_argument("config")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_apply)

    sp = sub.add_parser("view", help="show what is stored on each key per layer")
    sp.add_argument("--layer", type=int, choices=(1, 2, 3), help="only this layer")
    sp.set_defaults(func=cmd_view)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (keys.ParseError, ValueError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

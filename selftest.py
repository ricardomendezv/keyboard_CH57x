"""Offline check of the encoder against the reference device's known byte vectors.
No hardware needed. Run:  python selftest.py
"""
from keys import make_key_action, make_media_action, make_mouse_action, Press, KeyAction
from protocol import build_binding, encode, to_key_id

def H(s):  # "03 01 11" -> [3,1,17]
    return [int(x, 16) for x in s.split()]

cases = []

# Ctrl+A on KEY1, layer 0  (reference: start / header / press / finish)
msgs = build_binding("KEY1", 0, make_key_action("ctrl+a"))
cases.append(("kbd ctrl+a KEY1", msgs, [
    H("03 FE 01 01 01"), H("03 01 11 01"), H("03 01 11 01 01 01 04"), H("03 AA AA"),
]))

# Media Volume Up on KEY2, layer 0
msgs = build_binding("KEY2", 0, make_media_action("volume_up"))
cases.append(("media volup KEY2", msgs, [
    H("03 FE 01 01 01"), H("03 02 12 E9 00"), H("03 AA AA"),
]))

# Mouse left click KEY3
msgs = encode(to_key_id("KEY3"), 0, make_mouse_action("left_click"))
cases.append(("mouse click KEY3 (payload only)", msgs, [H("03 03 13 01 00 00 00 00")]))

# Mouse move (10,-5) KEY4
msgs = encode(to_key_id("KEY4"), 0, make_mouse_action({"move": [10, -5]}))
cases.append(("mouse move KEY4", msgs, [H("03 04 13 00 0A FB 00 00")]))

# Mouse wheel +3 KEY5
msgs = encode(to_key_id("KEY5"), 0, make_mouse_action({"wheel": 3}))
cases.append(("mouse wheel KEY5", msgs, [H("03 05 13 00 00 00 03 00")]))

# Mouse drag left (5,10) KEY6
msgs = encode(to_key_id("KEY6"), 0, make_mouse_action({"drag": "left", "move": [5, 10]}))
cases.append(("mouse drag KEY6", msgs, [H("03 06 13 01 05 0A 00 00")]))

# Knob ids
knob_ids = {t: to_key_id(t) for t in ("K1L", "K1P", "K1R", "K2L", "K2P", "K2R", "K3R")}

# 5-key macro "hello" (uppercase H -> shift)
macro = make_key_action("Hello")
cases.append(("macro 'Hello' presses", [[p.modifier, p.code] for p in macro.presses],
              [[0x02, 0x0B], [0, 0x08], [0, 0x0F], [0, 0x0F], [0, 0x12]]))

ok = True
for name, got, want in cases:
    # compare ignoring trailing zeros differences in mouse payloads
    def norm(seq):
        return [list(m) for m in seq]
    g, w = norm(got), norm(want)
    passed = g == w
    print(("PASS" if passed else "FAIL"), name)
    if not passed:
        ok = False
        print("   got :", g)
        print("   want:", w)

print("\nknob ids:", knob_ids, "(expect K1L=13,K1P=14,K1R=15,K2L=16,K2P=17,K2R=18,K3R=21)")
print("\nALL GOOD" if ok else "\nMISMATCH -- do not flash the device")

"""GUI for the CH57x macropad — layout mirrors the physical device.

Two knobs at top (circles + 3 actions each), 3×4 key grid below.
Run:  python gui.py
"""
from __future__ import annotations
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


import keys
from keys import SHORTCUTS, MEDIA, parse_action
from protocol import Keypad, DeviceNotFound, build_binding, hexdump, to_key_id, ALL_TARGETS
from store import Profile, LAYERS


def _spec_str(spec) -> str:
    return spec if isinstance(spec, str) else json.dumps(spec)


KEY_TARGETS = [f"KEY{i}" for i in range(1, 13)]
KNOB_TARGETS = {
    1: [("K1L", "⟵"), ("K1P", "●"), ("K1R", "⟶")],
    2: [("K2L", "⟵"), ("K2P", "●"), ("K2R", "⟶")],
    3: [("K3L", "⟵"), ("K3P", "●"), ("K3R", "⟶")],
}

SUGGESTIONS = (
    sorted(SHORTCUTS)
    + ["media:" + m for m in sorted(MEDIA)]
    + ["mouse:left_click", "mouse:right_click", "mouse:middle_click",
       "mouse:wheel_up", "mouse:wheel_down"]
    + ["ctrl+alt+del", "alt+tab", "f5"]
)

_KR = 30  # knob circle radius in px


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.layer = tk.IntVar(value=1)
        self.fields: dict[str, tk.StringVar] = {}
        self.profile = Profile.load()

        self._build_top()
        self._build_body()
        self._build_log()
        self._load_layer_into_fields()
        self.refresh_status()

    # ── top status bar ──────────────────────────────────────────────────────
    def _build_top(self):
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.status = ttk.Label(top, text="…", font=("Segoe UI", 10, "bold"))
        self.status.pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_status).pack(side="left", padx=6)

        ttk.Label(top, text="   Layer:").pack(side="left")
        for n in (1, 2, 3):
            ttk.Radiobutton(top, text=str(n), value=n, variable=self.layer,
                            command=self.on_layer_change).pack(side="left")

        ttk.Button(top, text="View all", command=self.view_all).pack(side="right")

    # ── device body: knobs + key grid ───────────────────────────────────────
    def _build_body(self):
        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        # ── Knob row (2 knobs side-by-side) ──
        knob_row = ttk.Frame(body)
        knob_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        knob_row.columnconfigure(0, weight=1)
        knob_row.columnconfigure(1, weight=1)

        for col, k in enumerate([1, 2]):
            kf = ttk.LabelFrame(knob_row, text=f"Knob {k}", padding=6)
            kf.grid(row=0, column=col, padx=6, sticky="nsew")
            kf.columnconfigure(1, weight=1)

            # Circular knob graphic with a top-position indicator dot
            d = _KR * 2 + 4
            c = tk.Canvas(kf, width=d, height=d, highlightthickness=0, bg="#ececec")
            c.create_oval(2, 2, d - 2, d - 2, fill="#d0d0d0", outline="#777", width=2)
            cx = d // 2
            c.create_oval(cx - 3, 5, cx + 3, 11, fill="#555", outline="")
            c.grid(row=0, column=0, columnspan=3, pady=(0, 6))

            for r, (target, sym) in enumerate(KNOB_TARGETS[k]):
                ttk.Label(kf, text=sym, width=2, anchor="center",
                      font=("Segoe UI", 13, "bold")).grid(
                    row=r + 1, column=0, padx=(0, 2))
                var = tk.StringVar()
                self.fields[target] = var
                ttk.Combobox(kf, textvariable=var, values=SUGGESTIONS, width=16).grid(
                    row=r + 1, column=1, sticky="ew", pady=1)
                ttk.Button(kf, text="▶", width=2,
                           command=lambda t=target: self.program_one(t)).grid(
                    row=r + 1, column=2, padx=(2, 0))

        # ── 3×4 key grid ──
        kp = ttk.LabelFrame(body, text="Keys", padding=6)
        kp.grid(row=1, column=0, sticky="nsew", padx=4)
        for c in range(3):
            kp.columnconfigure(c, weight=1)

        for i, key in enumerate(KEY_TARGETS):
            col, row = i // 4, 3 - (i % 4)
            kp.rowconfigure(row, weight=1)
            cell = ttk.LabelFrame(kp, text=f"KEY {row * 3 + col + 1}", padding=4)
            cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            cell.columnconfigure(0, weight=1)
            var = tk.StringVar()
            self.fields[key] = var
            ttk.Combobox(cell, textvariable=var, values=SUGGESTIONS, width=12).grid(
                row=0, column=0, sticky="ew")
            ttk.Button(cell, text="▶", width=2,
                       command=lambda t=key: self.program_one(t)).grid(
                row=0, column=1, padx=(2, 0))

    # ── action bar + log ────────────────────────────────────────────────────
    def _build_log(self):
        bar = ttk.Frame(self)
        bar.grid(row=2, column=0, sticky="ew", pady=6)
        ttk.Button(bar, text="Program ALL", command=self.program_all).pack(side="left")
        ttk.Button(bar, text="Preview bytes", command=self.preview).pack(side="left", padx=4)
        ttk.Button(bar, text="Load JSON…", command=self.load_json).pack(side="left", padx=4)
        ttk.Button(bar, text="Save JSON…", command=self.save_json).pack(side="left")

        self.log = tk.Text(self, height=7, wrap="word")
        self.log.grid(row=3, column=0, sticky="ew")

    def say(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    # ── status ──────────────────────────────────────────────────────────────
    def refresh_status(self):
        if Keypad.is_connected():
            self.status.config(text="● Connected (CH57x 1189:8890)", foreground="green")
        else:
            self.status.config(text="● Not connected — plug in the macropad", foreground="red")

    # ── layer / profile ──────────────────────────────────────────────────────
    def _load_layer_into_fields(self):
        data = self.profile.get_layer(self.layer.get())
        for target, var in self.fields.items():
            spec = data.get(target)
            var.set(_spec_str(spec) if spec is not None else "")

    def on_layer_change(self):
        self._load_layer_into_fields()
        self.say(f"Showing layer {self.layer.get()} (stored bindings).")

    def _record(self, layer1: int, target: str, spec):
        self.profile.set(layer1, target, spec)
        self.profile.save()

    def view_all(self):
        win = tk.Toplevel(self)
        win.title("Stored bindings — all layers")
        win.geometry("520x560")
        txt = tk.Text(win, wrap="none")
        txt.pack(fill="both", expand=True)
        txt.insert("end", f"(file: {self.profile.path})\n")
        for L in LAYERS:
            data = self.profile.get_layer(L)
            txt.insert("end", f"\n== Layer {L} ==\n")
            for t in ALL_TARGETS:
                spec = data.get(t)
                txt.insert("end", f"  {t:<6} {_spec_str(spec) if spec is not None else '-'}\n")
        txt.configure(state="disabled")

    # ── programming ──────────────────────────────────────────────────────────
    def _collect(self):
        layer0 = self.layer.get() - 1
        for target, var in self.fields.items():
            spec = var.get().strip()
            if not spec:
                continue
            yield target, layer0, parse_action(spec)

    def preview(self):
        self.log.delete("1.0", "end")
        try:
            any_ = False
            for target, layer0, action in self._collect():
                any_ = True
                self.say(f"# {target} (layer {layer0 + 1})")
                self.say(hexdump(build_binding(target, layer0, action)))
                self.say("")
            if not any_:
                self.say("Nothing to preview — fill in at least one field.")
        except (keys.ParseError, ValueError) as e:
            self.say(f"ERROR: {e}")

    def _program(self, items) -> bool:
        try:
            items = list(items)
        except (keys.ParseError, ValueError) as e:
            messagebox.showerror("Bad binding", str(e))
            return False
        if not items:
            self.say("Nothing to program.")
            return False
        try:
            with Keypad() as kp:
                for target, layer0, action in items:
                    kp.program(target, layer0, action)
                    self.say(f"programmed {target} (layer {layer0 + 1})")
            self.say("Done.")
            return True
        except DeviceNotFound as e:
            messagebox.showerror("Device not found", str(e))
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Write failed", str(e))
        return False

    def program_one(self, target):
        spec = self.fields[target].get().strip()
        if not spec:
            self.say(f"{target}: empty, skipped.")
            return
        try:
            action = parse_action(spec)
            to_key_id(target)
        except (keys.ParseError, ValueError) as e:
            messagebox.showerror("Bad binding", f"{target}: {e}")
            return
        if self._program([(target, self.layer.get() - 1, action)]):
            self._record(self.layer.get(), target, spec)

    def program_all(self):
        layer1 = self.layer.get()
        specs = [(t, v.get().strip()) for t, v in self.fields.items() if v.get().strip()]
        if self._program(self._collect()):
            for target, spec in specs:
                self._record(layer1, target, spec)

    # ── JSON ─────────────────────────────────────────────────────────────────
    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        if "layer" in cfg:
            self.layer.set(cfg["layer"])
        for b in cfg.get("bindings", []):
            target = b["target"].upper()
            if target in self.fields:
                act = b.get("action", "")
                self.fields[target].set(act if isinstance(act, str) else json.dumps(act))
        self.say(f"Loaded {path}")

    def save_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        bindings = [{"target": t, "action": v.get().strip()}
                    for t, v in self.fields.items() if v.get().strip()]
        cfg = {"layer": self.layer.get(), "bindings": bindings}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        self.say(f"Saved {path}")


def main():
    root = tk.Tk()
    root.title("Mini Keyboard — Python (CH57x)")
    root.geometry("580x780")
    try:
        root.iconbitmap(resource_path("app.ico"))
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

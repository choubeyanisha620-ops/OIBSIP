"""
Random Password Generator - GUI Version
=========================================
A polished Tkinter desktop application with:
  • Password length input
  • Checkboxes for letters, numbers, symbols
  • Exclude-similar-characters toggle
  • Generate button
  • Password display with copy-to-clipboard
  • Animated strength indicator (Weak / Medium / Strong)
"""

import random
import string
import tkinter as tk
from tkinter import messagebox

# ── optional clipboard support ──────────────────────────────────────────────
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

# ──────────────────────────────────────────────────────────────────────────────
#  CORE LOGIC  (shared with CLI; no GUI dependencies)
# ──────────────────────────────────────────────────────────────────────────────
SIMILAR_CHARS = set("0Ol1I|")


def filter_similar(chars: str) -> str:
    return "".join(c for c in chars if c not in SIMILAR_CHARS)


def get_pool_and_guaranteed(use_letters, use_numbers, use_symbols,
                            exclude_similar):
    pool, guaranteed = "", []

    if use_letters:
        upper = string.ascii_uppercase
        lower = string.ascii_lowercase
        if exclude_similar:
            upper, lower = filter_similar(upper), filter_similar(lower)
        pool += upper + lower
        guaranteed += [random.choice(upper), random.choice(lower)]

    if use_numbers:
        nums = string.digits
        if exclude_similar:
            nums = filter_similar(nums)
        pool += nums
        guaranteed.append(random.choice(nums))

    if use_symbols:
        syms = string.punctuation
        if exclude_similar:
            syms = filter_similar(syms)
        pool += syms
        guaranteed.append(random.choice(syms))

    return pool, guaranteed


def generate_password(length, use_letters, use_numbers,
                      use_symbols, exclude_similar):
    pool, guaranteed = get_pool_and_guaranteed(
        use_letters, use_numbers, use_symbols, exclude_similar
    )
    extra = [random.choice(pool) for _ in range(length - len(guaranteed))]
    chars = guaranteed + extra
    random.shuffle(chars)
    return "".join(chars)


def evaluate_strength(password):
    score = 0
    if len(password) >= 8:  score += 1
    if len(password) >= 12: score += 1
    if any(c.isupper() for c in password):          score += 1
    if any(c.islower() for c in password):          score += 1
    if any(c.isdigit() for c in password):          score += 1
    if any(c in string.punctuation for c in password): score += 1

    if score <= 2: return "Weak",   "#e74c3c"   # red
    if score <= 4: return "Medium", "#f39c12"   # amber
    return          "Strong", "#27ae60"          # green


# ──────────────────────────────────────────────────────────────────────────────
#  THEME CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
BG          = "#0f0f1a"       # deep navy-black
CARD        = "#1a1a2e"       # slightly lighter panel
ACCENT      = "#7c5cbf"       # purple accent
ACCENT_GLOW = "#9b7fd4"
TEXT        = "#e8e8f0"
SUBTEXT     = "#8888aa"
BORDER      = "#2d2d4a"
ENTRY_BG    = "#12122a"
BTN_BG      = "#7c5cbf"
BTN_HOVER   = "#9b7fd4"
BTN_2       = "#1e3a5f"
BTN_2_HOVER = "#2a5080"

FONT_TITLE  = ("Courier New", 20, "bold")
FONT_LABEL  = ("Courier New", 10)
FONT_CB     = ("Courier New", 10)
FONT_BTN    = ("Courier New", 11, "bold")
FONT_PW     = ("Courier New", 14, "bold")
FONT_SMALL  = ("Courier New", 9)


# ──────────────────────────────────────────────────────────────────────────────
#  APPLICATION CLASS
# ──────────────────────────────────────────────────────────────────────────────
class PasswordGeneratorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._setup_window()
        self._build_ui()

    # ── window setup ─────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("🔐 Password Generator")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Centre on screen
        w, h = 480, 620
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=24)

        # ── Title ────────────────────────────────────────────────────────────
        tk.Label(self.root, text="🔐 PASSWORD GENERATOR",
                 font=FONT_TITLE, fg=ACCENT_GLOW, bg=BG).pack(pady=(28, 4))
        tk.Label(self.root, text="Craft unbreakable secrets",
                 font=FONT_SMALL, fg=SUBTEXT, bg=BG).pack(pady=(0, 20))

        # ── Card ─────────────────────────────────────────────────────────────
        card = tk.Frame(self.root, bg=CARD, bd=0, relief="flat",
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", **pad, pady=(0, 16))

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=20, pady=18)

        # ── Length ───────────────────────────────────────────────────────────
        row_len = tk.Frame(inner, bg=CARD)
        row_len.pack(fill="x", pady=(0, 12))
        tk.Label(row_len, text="PASSWORD LENGTH", font=FONT_LABEL,
                 fg=SUBTEXT, bg=CARD).pack(side="left")

        self.length_var = tk.IntVar(value=16)
        vcmd = (self.root.register(self._validate_int), "%P")
        self.length_entry = tk.Entry(
            row_len, textvariable=self.length_var, width=5,
            font=FONT_PW, bg=ENTRY_BG, fg=TEXT,
            insertbackground=ACCENT_GLOW, bd=0,
            highlightbackground=BORDER, highlightthickness=1,
            validate="key", validatecommand=vcmd, justify="center"
        )
        self.length_entry.pack(side="right")

        # ── Slider ───────────────────────────────────────────────────────────
        self.slider = tk.Scale(
            inner, from_=4, to=64, orient="horizontal",
            variable=self.length_var,
            bg=CARD, fg=TEXT, troughcolor=ENTRY_BG,
            activebackground=ACCENT, highlightthickness=0,
            showvalue=False, sliderlength=18, width=8
        )
        self.slider.pack(fill="x", pady=(0, 14))

        # ── Divider ──────────────────────────────────────────────────────────
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))

        # ── Checkboxes ───────────────────────────────────────────────────────
        self.var_letters  = tk.BooleanVar(value=True)
        self.var_numbers  = tk.BooleanVar(value=True)
        self.var_symbols  = tk.BooleanVar(value=True)
        self.var_similar  = tk.BooleanVar(value=False)

        options = [
            (self.var_letters, "Aa",  "Letters  (A-Z, a-z)"),
            (self.var_numbers, "123", "Numbers  (0-9)"),
            (self.var_symbols, "!@#", "Symbols  (!@#…)"),
        ]
        for var, badge, label in options:
            self._checkbox_row(inner, var, badge, label)

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(10, 10))
        self._checkbox_row(inner, self.var_similar, "≠",
                           "Exclude similar chars  (0 O l 1 I)")

        # ── Generate button ──────────────────────────────────────────────────
        self.gen_btn = self._make_button(
            self.root, "⚡  GENERATE PASSWORD",
            self._on_generate, BTN_BG, BTN_HOVER
        )
        self.gen_btn.pack(fill="x", **pad, pady=(0, 10))

        # ── Password display ─────────────────────────────────────────────────
        pw_card = tk.Frame(self.root, bg=CARD,
                           highlightbackground=BORDER, highlightthickness=1)
        pw_card.pack(fill="x", **pad, pady=(0, 10))

        pw_inner = tk.Frame(pw_card, bg=CARD)
        pw_inner.pack(fill="x", padx=16, pady=14)

        tk.Label(pw_inner, text="GENERATED PASSWORD",
                 font=FONT_SMALL, fg=SUBTEXT, bg=CARD).pack(anchor="w")

        self.pw_var = tk.StringVar(value="—")
        tk.Label(pw_inner, textvariable=self.pw_var,
                 font=FONT_PW, fg=ACCENT_GLOW, bg=CARD,
                 wraplength=390, justify="left").pack(anchor="w", pady=(4, 0))

        # ── Strength bar ─────────────────────────────────────────────────────
        bar_frame = tk.Frame(pw_inner, bg=CARD)
        bar_frame.pack(fill="x", pady=(10, 0))

        tk.Label(bar_frame, text="STRENGTH", font=FONT_SMALL,
                 fg=SUBTEXT, bg=CARD).pack(side="left")
        self.strength_label = tk.Label(bar_frame, text="—",
                                       font=("Courier New", 9, "bold"),
                                       fg=SUBTEXT, bg=CARD)
        self.strength_label.pack(side="right")

        self.bar_bg = tk.Frame(pw_inner, bg=BORDER, height=6)
        self.bar_bg.pack(fill="x", pady=(4, 0))
        self.bar_fill = tk.Frame(self.bar_bg, bg=BORDER, height=6, width=0)
        self.bar_fill.place(x=0, y=0, relheight=1)

        # ── Copy button ──────────────────────────────────────────────────────
        self.copy_btn = self._make_button(
            self.root, "📋  COPY TO CLIPBOARD",
            self._on_copy, BTN_2, BTN_2_HOVER
        )
        self.copy_btn.pack(fill="x", **pad, pady=(0, 20))

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready — configure options and hit Generate.")
        tk.Label(self.root, textvariable=self.status_var,
                 font=FONT_SMALL, fg=SUBTEXT, bg=BG).pack(pady=(0, 10))

    # ── widget helpers ───────────────────────────────────────────────────────
    def _checkbox_row(self, parent, var, badge, label):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=3)

        tk.Label(row, text=badge, font=("Courier New", 9, "bold"),
                 fg=ACCENT_GLOW, bg=CARD, width=4).pack(side="left")

        cb = tk.Checkbutton(
            row, text=label, variable=var,
            font=FONT_CB, fg=TEXT, bg=CARD,
            activebackground=CARD, activeforeground=ACCENT_GLOW,
            selectcolor=ENTRY_BG, bd=0, highlightthickness=0,
            cursor="hand2"
        )
        cb.pack(side="left")

    def _make_button(self, parent, text, command, bg, hover_bg):
        btn = tk.Label(
            parent, text=text, font=FONT_BTN,
            fg=TEXT, bg=bg, cursor="hand2",
            pady=10
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>",    lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>",    lambda e: btn.configure(bg=bg))
        return btn

    # ── validation ───────────────────────────────────────────────────────────
    @staticmethod
    def _validate_int(value):
        return value == "" or (value.isdigit() and int(value) <= 64)

    # ── actions ──────────────────────────────────────────────────────────────
    def _on_generate(self):
        # Validate length
        try:
            length = int(self.length_entry.get())
            if length < 4:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Length",
                                   "Please enter a length between 4 and 64.")
            return

        use_letters = self.var_letters.get()
        use_numbers = self.var_numbers.get()
        use_symbols = self.var_symbols.get()
        exclude_sim = self.var_similar.get()

        if not any([use_letters, use_numbers, use_symbols]):
            messagebox.showwarning("No Character Types",
                                   "Select at least one character type.")
            return

        # Generate
        pw = generate_password(length, use_letters, use_numbers,
                               use_symbols, exclude_sim)
        self.pw_var.set(pw)

        # Strength
        label, colour = evaluate_strength(pw)
        self.strength_label.configure(text=label, fg=colour)

        # Animate bar width
        bar_w = self.bar_bg.winfo_width() or 420
        ratio  = {"Weak": 0.33, "Medium": 0.66, "Strong": 1.0}[label]
        self.bar_fill.configure(bg=colour)
        self.bar_fill.place(x=0, y=0, relheight=1,
                             width=int(bar_w * ratio))

        self.status_var.set(f"✅  Password generated — strength: {label}")

    def _on_copy(self):
        pw = self.pw_var.get()
        if pw in ("—", ""):
            self.status_var.set("⚠  Generate a password first!")
            return

        if HAS_PYPERCLIP:
            pyperclip.copy(pw)
            self.status_var.set("📋  Password copied to clipboard via pyperclip!")
        else:
            # Fallback: Tkinter's own clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(pw)
            self.root.update()
            self.status_var.set("📋  Password copied to clipboard!")


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

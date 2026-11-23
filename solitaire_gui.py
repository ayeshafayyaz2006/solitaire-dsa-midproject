"""
Graphical (Tkinter) interface for the Klondike Solitaire project.
Uses the SAME game logic / data structures from solitaire.py.

Run:  python solitaire_gui.py      (keep it in the same folder as solitaire.py)

Controls
  * Click the stock (top-left)       -> draw card(s)
  * Click a face-up card             -> select it (and the cards on top of it)
  * Click a destination pile         -> move there
  * Double-click a card              -> send it to the foundation
  * Buttons: New Game, Undo, Redo, Hint, Draw 1 / Draw 3
"""
import tkinter as tk
from tkinter import messagebox

from solitaire import (Solitaire, TABLEAU_KEYS, FOUNDATION_KEYS,
                       RANK_NAMES)

CARD_W, CARD_H = 80, 110
GAP = 20
MARGIN = 20
TOP_Y = 20
TABLEAU_Y = 170
DOWN_OFFSET = 18
UP_OFFSET = 30

SYMBOL = {'S': '\u2660', 'H': '\u2665', 'D': '\u2666', 'C': '\u2663'}
TABLE_GREEN = "#1f7a3f"


def col_x(col):
    return MARGIN + col * (CARD_W + GAP)


class SolitaireGUI:
    def __init__(self, root):
        self.root = root
        root.title("Klondike Solitaire - CSC200 DSA Project")
        root.configure(bg=TABLE_GREEN)
        self.draw_count = 1
        self.game = Solitaire(draw_count=self.draw_count)
        self.selected = None          # (pile_key, number_of_cards)
        self.regions = []             # clickable areas, rebuilt on every redraw
        self.message = "Welcome! Click the stock to draw."
        self.won_shown = False

        # ----- buttons -----
        bar = tk.Frame(root, bg=TABLE_GREEN)
        bar.pack(fill="x", pady=4)
        for text, cmd in [("New Game", self.new_game), ("Undo", self.undo),
                          ("Redo", self.redo), ("Hint", self.hint)]:
            tk.Button(bar, text=text, width=9, command=cmd).pack(side="left", padx=4)
        self.mode_btn = tk.Button(bar, text="Draw: 1", width=9,
                                  command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=4)
        self.info = tk.Label(bar, text="", bg=TABLE_GREEN, fg="white",
                             font=("Arial", 11, "bold"))
        self.info.pack(side="right", padx=10)

        # ----- canvas -----
        width = MARGIN * 2 + 7 * CARD_W + 6 * GAP
        self.canvas = tk.Canvas(root, width=width, height=640, bg=TABLE_GREEN,
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        self.status = tk.Label(root, text="", bg="#145a2d", fg="white",
                               anchor="w", font=("Arial", 10))
        self.status.pack(fill="x")

        self.redraw()
        self.tick()

    # ------------------------------------------------------------------ buttons
    def new_game(self):
        self.game = Solitaire(draw_count=self.draw_count)
        self.selected = None
        self.won_shown = False
        self.message = "New game started."
        self.redraw()

    def toggle_mode(self):
        self.draw_count = 3 if self.draw_count == 1 else 1
        self.mode_btn.config(text=f"Draw: {self.draw_count}")
        self.new_game()
        self.message = f"New game, drawing {self.draw_count} card(s) at a time."
        self.redraw()

    def undo(self):
        self.selected = None
        self.message = self.game.undo()[1]
        self.redraw()

    def redo(self):
        self.selected = None
        self.message = self.game.redo()[1]
        self.redraw()

    def hint(self):
        hs = self.game.hints()
        self.message = ("Hint: " + hs[0]) if hs else "No moves available. Try Undo or New Game."
        self.redraw()

    def tick(self):
        self.update_info()
        self.root.after(1000, self.tick)

    def update_info(self):
        t = self.game.elapsed()
        self.info.config(text=f"Score: {self.game.score}   Moves: {self.game.moves}"
                              f"   Time: {t // 60:02d}:{t % 60:02d}")

    # ------------------------------------------------------------------ drawing
    def card_label(self, card):
        return RANK_NAMES[card.rank - 1] + SYMBOL[card.suit]

    def draw_card(self, x, y, card, key, index, selected=False):
        if card.face_up:
            self.canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                         fill="white", outline="black", width=2)
            colour = "red" if card.color == 'R' else "black"
            label = self.card_label(card)
            self.canvas.create_text(x + 8, y + 6, text=label, anchor="nw",
                                    fill=colour, font=("Arial", 13, "bold"))
            self.canvas.create_text(x + CARD_W / 2, y + CARD_H / 2 + 8,
                                    text=SYMBOL[card.suit], fill=colour,
                                    font=("Arial", 30))
        else:
            self.canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                         fill="#2b4fa3", outline="white", width=2)
            self.canvas.create_rectangle(x + 8, y + 8, x + CARD_W - 8, y + CARD_H - 8,
                                         outline="#9db4ee")
        if selected:
            self.canvas.create_rectangle(x - 2, y - 2, x + CARD_W + 2, y + CARD_H + 2,
                                         outline="gold", width=4)

    def draw_empty(self, x, y, text=""):
        self.canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                     outline="#9fd3b1", width=2, dash=(4, 3))
        if text:
            self.canvas.create_text(x + CARD_W / 2, y + CARD_H / 2, text=text,
                                    fill="#9fd3b1", font=("Arial", 24))

    def add_region(self, x, y, w, h, kind, key, index=None):
        self.regions.append((x, y, x + w, y + h, kind, key, index))

    def redraw(self):
        g = self.game
        self.canvas.delete("all")
        self.regions = []

        # --- stock (column 0) ---
        x = col_x(0)
        if g.stock.is_empty():
            self.draw_empty(x, TOP_Y, "\u21bb")
        else:
            self.canvas.create_rectangle(x, TOP_Y, x + CARD_W, TOP_Y + CARD_H,
                                         fill="#2b4fa3", outline="white", width=2)
            self.canvas.create_text(x + CARD_W / 2, TOP_Y + CARD_H / 2,
                                    text=str(g.stock.size()), fill="white",
                                    font=("Arial", 20, "bold"))
        self.add_region(x, TOP_Y, CARD_W, CARD_H, "stock", "STOCK")

        # --- waste (column 1, fanned for draw-3) ---
        x = col_x(1)
        shown = g.waste.to_list()[-g.draw_count:]
        if not shown:
            self.draw_empty(x, TOP_Y)
        for i, card in enumerate(shown):
            cx = x + i * 22
            is_top = (i == len(shown) - 1)
            sel = self.selected == ('W', 1) and is_top
            self.draw_card(cx, TOP_Y, card, 'W', i, sel)
            if is_top:
                self.add_region(cx, TOP_Y, CARD_W, CARD_H, "card", 'W', g.waste.size() - 1)

        # --- foundations (columns 3..6) ---
        for i, key in enumerate(FOUNDATION_KEYS):
            x = col_x(3 + i)
            pile = g.foundation[key]
            if pile.is_empty():
                self.draw_empty(x, TOP_Y, SYMBOL[key[1]])
            else:
                sel = self.selected == (key, 1)
                self.draw_card(x, TOP_Y, pile.peek(), key, pile.size() - 1, sel)
            self.add_region(x, TOP_Y, CARD_W, CARD_H, "pile", key)

        # --- tableau ---
        for i, key in enumerate(TABLEAU_KEYS):
            x = col_x(i)
            cards = g.tableau[key].to_list()
            self.add_region(x, TABLEAU_Y, CARD_W, CARD_H, "pile", key)
            if not cards:
                self.draw_empty(x, TABLEAU_Y)
                continue
            y = TABLEAU_Y
            sel_from = None
            if self.selected and self.selected[0] == key:
                sel_from = len(cards) - self.selected[1]
            for idx, card in enumerate(cards):
                self.draw_card(x, y, card, key, idx,
                               selected=(sel_from is not None and idx >= sel_from))
                is_last = idx == len(cards) - 1
                height = CARD_H if is_last else (UP_OFFSET if card.face_up else DOWN_OFFSET)
                self.add_region(x, y, CARD_W, height, "card", key, idx)
                y += UP_OFFSET if card.face_up else DOWN_OFFSET

        self.update_info()
        self.status.config(text="  " + self.message)

        if g.is_won() and not self.won_shown:
            self.won_shown = True
            messagebox.showinfo("You won!",
                                f"Congratulations!\nScore: {g.score}\n"
                                f"Moves: {g.moves}\nTime: {g.elapsed()} seconds")

    # ------------------------------------------------------------------ clicking
    def find_region(self, x, y):
        for (x1, y1, x2, y2, kind, key, index) in reversed(self.regions):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return kind, key, index
        return None

    def try_select(self, key, index):
        g = self.game
        if key == 'W':
            self.selected = ('W', 1)
        elif key in TABLEAU_KEYS:
            cards = g.tableau[key].to_list()
            if index is None or index >= len(cards) or not cards[index].face_up:
                self.message = "Select a face-up card."
                return
            self.selected = (key, len(cards) - index)
        else:
            self.selected = (key, 1)
        self.message = "Card selected. Click where to move it."

    def on_click(self, event):
        hit = self.find_region(event.x, event.y)
        if hit is None:
            self.selected = None
            self.redraw()
            return
        kind, key, index = hit

        if kind == "stock":
            self.selected = None
            self.message = self.game.draw()[1]
            self.redraw()
            return

        if self.selected is None:
            if kind == "card" or (key in FOUNDATION_KEYS
                                  and not self.game.foundation[key].is_empty()):
                self.try_select(key, index)
            else:
                self.message = "Nothing to select there."
            self.redraw()
            return

        src, count = self.selected
        if key == src:                     # clicked same pile -> deselect
            self.selected = None
            self.message = "Selection cleared."
            self.redraw()
            return

        if key == 'W':                     # cannot move onto waste
            self.selected = None
            self.try_select(key, index)
            self.redraw()
            return

        ok, msg = self.game.move(src, key, count)
        self.selected = None
        self.message = "Moved." if ok else msg
        if not ok and kind == "card":      # failed: maybe user meant new selection
            self.try_select(key, index)
        self.redraw()

    def on_double_click(self, event):
        hit = self.find_region(event.x, event.y)
        self.selected = None
        if hit and hit[0] == "card":
            _, key, index = hit
            if key == 'W' or key in TABLEAU_KEYS:
                ok, msg = self.game.move(key, 'F', 1)
                self.message = "Moved to foundation." if ok else msg
        self.redraw()


def main():
    root = tk.Tk()
    SolitaireGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

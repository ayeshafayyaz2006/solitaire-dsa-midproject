"""
CSC200 - Data Structures & Algorithms | Mid Term Project
Klondike Solitaire (text based)

Data structures used (all written by hand, as the manual asks):
  Array/List  -> Deck (52 cards before shuffle + deal)
  Stack       -> Foundation piles + Waste pile + Undo/Redo history
  Queue       -> Stockpile (draw pile, FIFO)
  Linked List -> Tableau piles
  Dictionary  -> piles map (name -> pile) and location map (card -> pile name)
"""
import random
import time

# ----------------------------------------------------------------------------
# PHASE 1 : CARD AND DECK
# ----------------------------------------------------------------------------
SUITS = ['S', 'H', 'D', 'C']                      # Spades Hearts Diamonds Clubs
RANK_NAMES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RED_SUITS = ('H', 'D')


class Card:
    """A single playing card: suit, rank (1..13) and face-up/down state."""

    def __init__(self, suit, rank, face_up=False):
        self.suit = suit
        self.rank = rank
        self.face_up = face_up

    @property
    def color(self):
        return 'R' if self.suit in RED_SUITS else 'B'

    @property
    def name(self):                       # e.g. "10H", "AS"
        return RANK_NAMES[self.rank - 1] + self.suit

    def __str__(self):
        return self.name if self.face_up else '##'

    __repr__ = __str__


class Deck:
    """Array/List of 52 cards. Shuffle = Fisher-Yates algorithm."""

    def __init__(self):
        self.cards = [Card(s, r) for s in SUITS for r in range(1, 14)]

    def shuffle(self, rng=random):
        for i in range(len(self.cards) - 1, 0, -1):
            j = rng.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def deal_card(self):
        return self.cards.pop()

    def size(self):
        return len(self.cards)


# ----------------------------------------------------------------------------
# DATA STRUCTURES
# ----------------------------------------------------------------------------
class Stack:
    """LIFO stack (array based). Used for foundation, waste, undo/redo."""

    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        return self._items[-1] if self._items else None

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def clear(self):
        self._items = []

    def to_list(self):                    # bottom -> top
        return list(self._items)


class QueueNode:
    def __init__(self, card):
        self.card = card
        self.next = None


class Queue:
    """FIFO queue (linked nodes). Used for the stockpile.
    push_front is only needed so UNDO can put a drawn card back in place."""

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def enqueue(self, card):              # add at back
        node = QueueNode(card)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def dequeue(self):                    # remove from front
        if self.head is None:
            raise IndexError("dequeue from empty queue")
        node = self.head
        self.head = node.next
        if self.head is None:
            self.tail = None
        self._size -= 1
        return node.card

    def push_front(self, card):           # used by undo only
        node = QueueNode(card)
        node.next = self.head
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def to_list(self):                    # front -> back
        out, cur = [], self.head
        while cur:
            out.append(cur.card)
            cur = cur.next
        return out


class Node:
    def __init__(self, card):
        self.card = card
        self.next = None


class LinkedList:
    """Singly linked list = one tableau column.
    head = bottom card of the column, tail = top (playable) card."""

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def append(self, card):
        node = Node(card)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def peek(self):                       # top card
        return self.tail.card if self.tail else None

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def to_list(self):                    # bottom -> top
        out, cur = [], self.head
        while cur:
            out.append(cur.card)
            cur = cur.next
        return out

    def remove_last(self, n):
        """Cut the last n cards off the list and return them (in order)."""
        if n < 1 or n > self._size:
            raise IndexError("invalid number of cards")
        keep = self._size - n
        if keep == 0:
            removed = self.to_list()
            self.head = self.tail = None
        else:
            cur = self.head
            for _ in range(keep - 1):
                cur = cur.next
            removed, node = [], cur.next
            while node:
                removed.append(node.card)
                node = node.next
            cur.next = None
            self.tail = cur
        self._size = keep
        return removed


# ----------------------------------------------------------------------------
# PHASE 2 + 3 : GAME (tableau, foundation, rules, moves, undo/redo)
# ----------------------------------------------------------------------------
TABLEAU_KEYS = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
FOUNDATION_KEYS = ['FS', 'FH', 'FD', 'FC']


class Solitaire:
    def __init__(self, draw_count=1, seed=None):
        self.draw_count = draw_count      # 1 or 3 cards per draw
        self.rng = random.Random(seed)
        self.new_game()

    # ---------- setup ----------
    def reset_board(self):
        self.tableau = {k: LinkedList() for k in TABLEAU_KEYS}   # dictionary
        self.foundation = {k: Stack() for k in FOUNDATION_KEYS}  # dictionary
        self.waste = Stack()
        self.stock = Queue()
        self.location = {}      # HashMap: card name -> pile name
        self.undo_stack = Stack()
        self.redo_stack = Stack()
        self.score = 0
        self.moves = 0
        self.start_time = time.time()

    def new_game(self):
        self.reset_board()
        deck = Deck()
        deck.shuffle(self.rng)
        # deal 7 piles: pile i gets i cards, only the last is face up
        for i, key in enumerate(TABLEAU_KEYS, start=1):
            for j in range(i):
                card = deck.deal_card()
                card.face_up = (j == i - 1)
                self.tableau[key].append(card)
                self.location[card.name] = key
        # remaining 24 cards -> stockpile queue
        while deck.size() > 0:
            card = deck.deal_card()
            self.stock.enqueue(card)
            self.location[card.name] = 'STOCK'

    # ---------- helpers ----------
    def _pile(self, key):
        if key == 'W':
            return self.waste
        if key in self.tableau:
            return self.tableau[key]
        return self.foundation[key]

    def _remove(self, key, n):
        pile = self._pile(key)
        if isinstance(pile, LinkedList):
            return pile.remove_last(n)
        return [pile.pop()]

    def _add(self, key, cards):
        pile = self._pile(key)
        for c in cards:
            if isinstance(pile, LinkedList):
                pile.append(c)
            else:
                pile.push(c)
            self.location[c.name] = key

    def _moving_cards(self, src, count):
        """The cards that WOULD move (bottom->top), without removing them."""
        pile = self._pile(src)
        if isinstance(pile, LinkedList):
            return pile.to_list()[-count:]
        top = pile.peek()
        return [top] if top else []

    def elapsed(self):
        return int(time.time() - self.start_time)

    # ---------- validation ----------
    def validate_move(self, src, dst, count=1):
        valid_src = ['W'] + TABLEAU_KEYS + FOUNDATION_KEYS
        valid_dst = TABLEAU_KEYS + FOUNDATION_KEYS
        if src not in valid_src or dst not in valid_dst:
            return False, "Unknown pile name."
        if src == dst:
            return False, "Source and destination are the same."
        pile = self._pile(src)
        if pile.is_empty():
            return False, "Source pile is empty."
        if src not in TABLEAU_KEYS and count != 1:
            return False, "Only one card can be taken from there."
        if count < 1 or count > pile.size():
            return False, "Not enough cards in that pile."

        cards = self._moving_cards(src, count)
        if not all(c.face_up for c in cards):
            return False, "You cannot move face-down cards."
        first = cards[0]

        if dst in FOUNDATION_KEYS:
            if src in FOUNDATION_KEYS:
                return False, "Cannot move between foundations."
            if count != 1:
                return False, "Only one card at a time to the foundation."
            if first.suit != dst[1]:
                return False, "Wrong suit for that foundation."
            top = self.foundation[dst].peek()
            if top is None:
                if first.rank != 1:
                    return False, "Foundation must start with an Ace."
            elif first.rank != top.rank + 1:
                return False, "Foundation needs the next rank (Ace -> King)."
            return True, "OK"

        # destination is a tableau pile
        top = self.tableau[dst].peek()
        if top is None:
            if first.rank != 13:
                return False, "Only a King can go on an empty column."
        else:
            if not top.face_up:
                return False, "Destination top card is face down."
            if top.color == first.color:
                return False, "Colors must alternate (red on black)."
            if top.rank != first.rank + 1:
                return False, "Rank must be one lower than the destination."
        return True, "OK"

    def resolve_foundation(self, src, count=1):
        """If the player types 'F' as destination, pick the right suit pile."""
        if src in ['W'] + TABLEAU_KEYS and not self._pile(src).is_empty():
            return 'F' + self._moving_cards(src, 1 if src == 'W' else 1)[-1].suit
        return None

    # ---------- performing moves ----------
    def _push_history(self, record):
        self.undo_stack.push(record)
        self.redo_stack.clear()
        self.score += record['delta']
        self.moves += 1

    def move(self, src, dst, count=1):
        if dst == 'F':
            dst = self.resolve_foundation(src, count) or 'F'
        ok, msg = self.validate_move(src, dst, count)
        if not ok:
            return False, msg

        delta = 0
        if dst in FOUNDATION_KEYS:
            delta += 10
        elif src == 'W':
            delta += 5
        elif src in FOUNDATION_KEYS:
            delta -= 15

        flipped = False
        if src in TABLEAU_KEYS:
            pile = self.tableau[src]
            if pile.size() > count:
                below = pile.to_list()[-count - 1]
                if not below.face_up:
                    flipped = True
                    delta += 5

        record = {'type': 'move', 'src': src, 'dst': dst, 'count': count,
                  'flipped': flipped, 'delta': delta}
        self._apply(record)
        self._push_history(record)
        return True, "Moved."

    def draw(self):
        if self.stock.is_empty():
            if self.waste.is_empty():
                return False, "No cards left to draw."
            n = self.waste.size()
            record = {'type': 'recycle', 'n': n, 'delta': -20}
        else:
            n = min(self.draw_count, self.stock.size())
            record = {'type': 'draw', 'n': n, 'delta': 0}
        self._apply(record)
        self._push_history(record)
        return True, "Drew." if record['type'] == 'draw' else "Stock recycled."

    # ---------- apply / reverse a record (used by move, undo, redo) ----------
    def _apply(self, r):
        if r['type'] == 'draw':
            for _ in range(r['n']):
                c = self.stock.dequeue()          # FIFO
                c.face_up = True
                self.waste.push(c)
                self.location[c.name] = 'W'
        elif r['type'] == 'recycle':
            for c in self.waste.to_list():        # bottom -> top keeps order
                c.face_up = False
                self.stock.enqueue(c)
                self.location[c.name] = 'STOCK'
            self.waste.clear()
        else:  # move
            cards = self._remove(r['src'], r['count'])
            if r['flipped']:
                self.tableau[r['src']].peek().face_up = True
            self._add(r['dst'], cards)

    def _reverse(self, r):
        if r['type'] == 'draw':
            for _ in range(r['n']):
                c = self.waste.pop()
                c.face_up = False
                self.stock.push_front(c)
                self.location[c.name] = 'STOCK'
        elif r['type'] == 'recycle':
            for _ in range(r['n']):
                c = self.stock.dequeue()
                c.face_up = True
                self.waste.push(c)
                self.location[c.name] = 'W'
        else:  # move
            if r['flipped']:
                self.tableau[r['src']].peek().face_up = False
            cards = self._remove(r['dst'], r['count'])
            self._add(r['src'], cards)

    # ---------- undo / redo ----------
    def undo(self):
        if self.undo_stack.is_empty():
            return False, "Nothing to undo."
        r = self.undo_stack.pop()
        self._reverse(r)
        self.redo_stack.push(r)
        self.score -= r['delta']
        self.moves -= 1
        return True, "Undone."

    def redo(self):
        if self.redo_stack.is_empty():
            return False, "Nothing to redo."
        r = self.redo_stack.pop()
        self._apply(r)
        self.undo_stack.push(r)
        self.score += r['delta']
        self.moves += 1
        return True, "Redone."

    # ---------- win condition ----------
    def is_won(self):
        return sum(p.size() for p in self.foundation.values()) == 52

    # ---------- hint system ----------
    def hints(self):
        out = []
        sources = ['W'] + TABLEAU_KEYS
        for src in sources:
            pile = self._pile(src)
            if pile.is_empty() or not pile.peek().face_up:
                continue
            fdst = 'F' + pile.peek().suit
            if self.validate_move(src, fdst, 1)[0]:
                out.append(f"m {src} F      ({pile.peek().name} to foundation)")
        for src in sources:
            pile = self._pile(src)
            if pile.is_empty():
                continue
            if src == 'W':
                counts = [1]
            else:
                faceup = sum(1 for c in pile.to_list() if c.face_up)
                counts = range(1, faceup + 1)
            for count in counts:
                card = self._moving_cards(src, count)[0]
                if src != 'W' and card.rank == 13 and count == pile.size():
                    continue          # King already at the bottom: pointless
                for dst in TABLEAU_KEYS:
                    if self.validate_move(src, dst, count)[0]:
                        cmd = f"m {src} {dst}" + (f" {count}" if count > 1 else "")
                        out.append(f"{cmd:<12} ({card.name} onto "
                                   f"{self.tableau[dst].peek().name if not self.tableau[dst].is_empty() else 'empty column'})")
        if not out and (not self.stock.is_empty() or not self.waste.is_empty()):
            out.append("d            (draw from stock)")
        return out

    # ---------- PHASE 4 : text user interface ----------
    def display(self):
        print("\n" + "=" * 60)
        t = self.elapsed()
        print(f"Score: {self.score}   Moves: {self.moves}   "
              f"Time: {t // 60:02d}:{t % 60:02d}   Draw: {self.draw_count}")
        shown = self.waste.to_list()[-self.draw_count:]
        waste_txt = ' '.join(c.name for c in shown) if shown else '--'
        print(f"Stock: [{self.stock.size():>2}]   Waste(W): {waste_txt}"
              f"  (total {self.waste.size()})")
        found = '  '.join(
            f"{k}:{self.foundation[k].peek().name if not self.foundation[k].is_empty() else '--'}"
            for k in FOUNDATION_KEYS)
        print("Foundations:", found)
        print("-" * 60)
        print("  " + "".join(f"{k:<7}" for k in TABLEAU_KEYS))
        cols = [self.tableau[k].to_list() for k in TABLEAU_KEYS]
        height = max(len(c) for c in cols) if cols else 0
        for row in range(height):
            line = "  "
            for col in cols:
                if row < len(col):
                    card = col[row]
                    line += f"{('[' + str(card) + ']'):<7}"
                else:
                    line += " " * 7
            print(line)
        print("=" * 60)


HELP = """Commands:
  d               draw from stock (recycles waste when stock is empty)
  m SRC DST [n]   move n cards (default 1) from SRC to DST
                  SRC: W (waste), T1-T7, FS/FH/FD/FC   DST: T1-T7, F (auto), FS..
                  short form: 'm 3 5' means T3 -> T5,  'm w 2' means W -> T2
  u / r           undo / redo
  h               hint
  n               new game
  q               quit
Examples:  m W T3   |   m T1 F   |   m T2 T6 3"""


def norm(tok):
    tok = tok.upper()
    return 'T' + tok if tok.isdigit() else tok


def main():
    print("=== KLONDIKE SOLITAIRE ===")
    mode = input("Draw 1 or 3 cards? [1/3]: ").strip()
    game = Solitaire(draw_count=3 if mode == '3' else 1)
    print(HELP)
    while True:
        game.display()
        if game.is_won():
            print(f"*** YOU WON! Score {game.score}, time {game.elapsed()}s ***")
            break
        parts = input("> ").strip().split()
        if not parts:
            continue
        cmd = parts[0].lower()
        if cmd == 'q':
            break
        elif cmd == 'd':
            ok, msg = game.draw()
        elif cmd == 'u':
            ok, msg = game.undo()
        elif cmd == 'r':
            ok, msg = game.redo()
        elif cmd == 'h':
            hs = game.hints()
            print("Hints:" if hs else "No moves available.")
            for h in hs[:5]:
                print("  ", h)
            continue
        elif cmd == 'n':
            game.new_game()
            continue
        elif cmd == 'help':
            print(HELP)
            continue
        elif cmd == 'm' and len(parts) >= 3:
            try:
                count = int(parts[3]) if len(parts) > 3 else 1
            except ValueError:
                print("Count must be a number.")
                continue
            ok, msg = game.move(norm(parts[1]), norm(parts[2]), count)
        else:
            print("Unknown command. Type 'help'.")
            continue
        if not ok:
            print("!", msg)


if __name__ == "__main__":
    main()

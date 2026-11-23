"""Validation & Testing (manual section): legal moves, card flipping,
win condition, game flow, plus undo/redo and data structure checks.
Run:  python test_solitaire.py
"""
print('>>> test_solitaire.py is running...')
import unittest
from solitaire import (Card, Deck, Stack, Queue, LinkedList, Solitaire,
                       SUITS, TABLEAU_KEYS)


def C(rank, suit, up=True):
    return Card(suit, rank, up)


def blank_game():
    g = Solitaire(seed=1)
    g.reset_board()
    return g


class TestDeckAndSetup(unittest.TestCase):
    def test_deck_has_52_unique_cards(self):
        d = Deck()
        self.assertEqual(d.size(), 52)
        self.assertEqual(len({c.name for c in d.cards}), 52)

    def test_shuffle_changes_order(self):
        d1, d2 = Deck(), Deck()
        d2.shuffle()
        self.assertNotEqual([c.name for c in d1.cards], [c.name for c in d2.cards])

    def test_initial_deal(self):
        g = Solitaire(seed=5)
        for i, k in enumerate(TABLEAU_KEYS, start=1):
            cards = g.tableau[k].to_list()
            self.assertEqual(len(cards), i)
            self.assertTrue(cards[-1].face_up)
            self.assertTrue(all(not c.face_up for c in cards[:-1]))
        self.assertEqual(g.stock.size(), 24)
        self.assertEqual(len(g.location), 52)


class TestStructures(unittest.TestCase):
    def test_stack_lifo(self):
        s = Stack(); s.push(1); s.push(2)
        self.assertEqual(s.pop(), 2)
        self.assertEqual(s.pop(), 1)

    def test_queue_fifo(self):
        q = Queue(); q.enqueue('a'); q.enqueue('b')
        self.assertEqual(q.dequeue(), 'a')
        self.assertEqual(q.dequeue(), 'b')

    def test_linked_list_remove_last(self):
        ll = LinkedList()
        for r in range(1, 6):
            ll.append(C(r, 'S'))
        got = ll.remove_last(2)
        self.assertEqual([c.rank for c in got], [4, 5])
        self.assertEqual(ll.size(), 3)
        self.assertEqual(ll.peek().rank, 3)


class TestLegalMoves(unittest.TestCase):
    def test_alternating_color_and_rank(self):
        g = blank_game()
        g._add('T1', [C(8, 'S')])
        g._add('T2', [C(7, 'H')])
        g._add('T3', [C(7, 'C')])
        g._add('T4', [C(6, 'H')])
        self.assertTrue(g.move('T2', 'T1')[0])        # red 7 on black 8
        self.assertFalse(g.move('T3', 'T1')[0])       # black 7 on red 7: rank wrong
        self.assertTrue(g.move('T4', 'T3')[0])        # red 6 on black 7: legal

    def test_same_color_rejected(self):
        g = blank_game()
        g._add('T1', [C(8, 'S')]); g._add('T2', [C(7, 'C')])
        self.assertFalse(g.move('T2', 'T1')[0])

    def test_wrong_rank_rejected(self):
        g = blank_game()
        g._add('T1', [C(8, 'S')]); g._add('T2', [C(6, 'H')])
        self.assertFalse(g.move('T2', 'T1')[0])

    def test_only_king_on_empty(self):
        g = blank_game()
        g._add('T1', [C(12, 'H')]); g._add('T2', [C(13, 'S')])
        self.assertFalse(g.move('T1', 'T3')[0])
        self.assertTrue(g.move('T2', 'T3')[0])

    def test_foundation_ace_to_king(self):
        g = blank_game()
        g._add('T1', [C(2, 'H')]); g._add('T2', [C(1, 'H')])
        self.assertFalse(g.move('T1', 'F')[0])        # 2 before Ace
        self.assertTrue(g.move('T2', 'F')[0])
        self.assertTrue(g.move('T1', 'F')[0])
        self.assertEqual(g.foundation['FH'].size(), 2)

    def test_move_sequence(self):
        g = blank_game()
        g._add('T1', [C(9, 'S')])
        g._add('T2', [C(8, 'H'), C(7, 'S')])
        self.assertTrue(g.move('T2', 'T1', 2)[0])
        self.assertEqual(g.tableau['T1'].size(), 3)

    def test_cannot_move_face_down(self):
        g = blank_game()
        g._add('T1', [C(9, 'S')])
        g._add('T2', [C(8, 'H', False), C(7, 'S')])
        self.assertFalse(g.move('T2', 'T1', 2)[0])


class TestFlipping(unittest.TestCase):
    def test_flip_after_move(self):
        g = blank_game()
        g._add('T1', [C(3, 'C', False), C(7, 'H')])
        g._add('T2', [C(8, 'S')])
        self.assertTrue(g.move('T1', 'T2')[0])
        self.assertTrue(g.tableau['T1'].peek().face_up)


class TestStockAndUndo(unittest.TestCase):
    def test_draw_and_recycle_keep_order(self):
        g = Solitaire(draw_count=1, seed=3)
        order = [c.name for c in g.stock.to_list()]
        for _ in range(24):
            g.draw()
        self.assertTrue(g.stock.is_empty())
        g.draw()                                       # recycle
        self.assertEqual([c.name for c in g.stock.to_list()], order)

    def test_draw_three(self):
        g = Solitaire(draw_count=3, seed=3)
        g.draw()
        self.assertEqual(g.waste.size(), 3)
        self.assertEqual(g.stock.size(), 21)

    def test_undo_redo_draw(self):
        g = Solitaire(draw_count=3, seed=7)
        before = [c.name for c in g.stock.to_list()]
        g.draw()
        g.undo()
        self.assertEqual([c.name for c in g.stock.to_list()], before)
        self.assertTrue(g.waste.is_empty())
        g.redo()
        self.assertEqual(g.waste.size(), 3)

    def test_undo_redo_move_with_flip_and_score(self):
        g = blank_game()
        g._add('T1', [C(3, 'C', False), C(7, 'H')])
        g._add('T2', [C(8, 'S')])
        g.move('T1', 'T2')
        self.assertEqual(g.score, 5)
        g.undo()
        self.assertFalse(g.tableau['T1'].to_list()[0].face_up)
        self.assertEqual(g.tableau['T1'].size(), 2)
        self.assertEqual(g.score, 0)
        g.redo()
        self.assertTrue(g.tableau['T1'].peek().face_up)
        self.assertEqual(g.score, 5)

    def test_location_dictionary_updates(self):
        g = blank_game()
        g._add('T1', [C(7, 'H')]); g._add('T2', [C(8, 'S')])
        g.move('T1', 'T2')
        self.assertEqual(g.location['7H'], 'T2')


class TestWinAndFlow(unittest.TestCase):
    def test_win_detected(self):
        g = blank_game()
        self.assertFalse(g.is_won())
        for s in SUITS:
            for r in range(1, 14):
                g.foundation['F' + s].push(C(r, s))
        self.assertTrue(g.is_won())

    def test_hints_exist_and_game_flow(self):
        g = Solitaire(seed=11)
        self.assertIsInstance(g.hints(), list)
        for _ in range(30):                            # random play never crashes
            h = g.hints()
            if h and h[0].startswith('m'):
                p = h[0].split('(')[0].split()
                cnt = int(p[3]) if len(p) > 3 else 1
                dst = p[2]
                ok, _ = g.move(p[1], dst, cnt)
                self.assertTrue(ok)
            else:
                g.draw()
        total = (sum(p.size() for p in g.tableau.values())
                 + sum(p.size() for p in g.foundation.values())
                 + g.stock.size() + g.waste.size())
        self.assertEqual(total, 52)


def run_all_tests():
    """Runs every test and prints the result to the normal console
    (works in Spyder, IDLE, Jupyter and the terminal)."""
    import sys
    print("=" * 60)
    print("RUNNING SOLITAIRE TESTS")
    print("=" * 60)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    print("=" * 60)
    if result.wasSuccessful():
        print(f"ALL {result.testsRun} TESTS PASSED")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 60)


# runs both when you press F5 in Spyder and when you run: python test_solitaire.py
run_all_tests()
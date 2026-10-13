import random
import unittest
from game import Game2048


class GameRulesTests(unittest.TestCase):
    def make_game(self, board):
        game = Game2048(rng=random.Random(1234), start=False)
        game.board = [row[:] for row in board]
        return game

    def test_new_game_has_two_tiles(self):
        game = Game2048(rng=random.Random(1))
        self.assertEqual(sum(bool(v) for row in game.board for v in row), 2)
        self.assertEqual(game.score, 0)

    def test_collapse_merges_once(self):
        self.assertEqual(Game2048.collapse([2, 2, 2, 2]), ([4, 4, 0, 0], 8))
        self.assertEqual(Game2048.collapse([4, 4, 8, 0]), ([8, 8, 0, 0], 8))
        self.assertEqual(Game2048.collapse([2, 0, 2, 2]), ([4, 2, 0, 0], 4))

    def test_moving_left_adds_score_and_tile(self):
        game = self.make_game([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertTrue(game.move("left"))
        self.assertEqual(game.board[0][0], 4)
        self.assertEqual(game.score, 4)
        self.assertEqual(game.moves, 1)
        self.assertEqual(sum(bool(v) for row in game.board for v in row), 2)

    def test_invalid_move_does_not_change_board(self):
        game = self.make_game([[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertFalse(game.move("left"))
        self.assertEqual(game.moves, 0)

    def test_undo_restores_previous_state(self):
        game = self.make_game([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        original = game.snapshot()
        game.move("right")
        self.assertTrue(game.undo())
        self.assertEqual(game.snapshot(), original)
        self.assertFalse(game.undo())

    def test_no_possible_moves(self):
        game = self.make_game([[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
        self.assertFalse(game.can_move())
        self.assertFalse(game.spawn())

    def test_adjacent_equals_allow_moves(self):
        game = self.make_game([[2, 2, 4, 8], [4, 8, 16, 32], [8, 16, 32, 64], [16, 32, 64, 128]])
        self.assertTrue(game.can_move())

    def test_load_rejects_bad_data(self):
        game = Game2048(start=False)
        with self.assertRaises(ValueError):
            game.load({"board": [[2]], "score": 0, "moves": 0})
        with self.assertRaises(ValueError):
            game.load({"board": [[3] * 4 for _ in range(4)], "score": 0, "moves": 0})

    def test_win_at_2048(self):
        game = self.make_game([[1024, 1024, 0, 0], [0] * 4, [0] * 4, [0] * 4])
        game.move("left")
        self.assertTrue(game.won)


if __name__ == "__main__":
    unittest.main()

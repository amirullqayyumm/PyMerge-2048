"""Pure Python 2048 game rules, separate from browser-specific code."""

import random

SIZE = 4
TARGET = 2048
DIRECTIONS = {"up", "down", "left", "right"}


class Game2048:
    def __init__(self, rng=None, start=True):
        self.rng = rng or random.Random()
        self.board = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.moves = 0
        self.won = False
        self.over = False
        self.previous = None
        if start:
            self.spawn()
            self.spawn()

    def snapshot(self):
        return {
            "board": [row[:] for row in self.board],
            "score": self.score,
            "moves": self.moves,
            "won": self.won,
            "over": self.over,
        }

    def load(self, data):
        """Load a previously saved game. Reject malformed browser storage."""
        board = data["board"]
        if (not isinstance(board, list) or len(board) != SIZE or
                any(not isinstance(row, list) or len(row) != SIZE for row in board)):
            raise ValueError("Invalid board shape")
        for row in board:
            for v in row:
                if not isinstance(v, int) or isinstance(v, bool) or v < 0 or (v and v & (v - 1)):
                    raise ValueError("Invalid tile")
        score, moves = data["score"], data["moves"]
        if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in [score, moves]):
            raise ValueError("Invalid score")
        self.board = [row[:] for row in board]
        self.score = score
        self.moves = moves
        self.won = bool(data.get("won", False))
        self.over = bool(data.get("over", False))
        self.previous = None

    def spawn(self):
        empty = [(r, c) for r in range(SIZE) for c in range(SIZE)
                 if self.board[r][c] == 0]
        if not empty:
            return False
        r, c = self.rng.choice(empty)
        self.board[r][c] = 4 if self.rng.random() < 0.1 else 2
        return True

    @staticmethod
    def collapse(line):
        """Slide and merge one line toward its beginning."""
        values = [v for v in line if v]
        merged = []
        points = 0
        i = 0
        while i < len(values):
            if i + 1 < len(values) and values[i] == values[i + 1]:
                v = values[i] * 2
                merged.append(v)
                points += v
                i += 2
            else:
                merged.append(values[i])
                i += 1
        return merged + [0] * (SIZE - len(merged)), points

    def move(self, direction):
        if direction not in DIRECTIONS:
            raise ValueError("Unknown direction")
        if self.over:
            return False
        original = self.snapshot()
        updated = [[0] * SIZE for _ in range(SIZE)]
        gained = 0

        for i in range(SIZE):
            if direction in ("left", "right"):
                line = self.board[i][:]
            else:
                line = [self.board[r][i] for r in range(SIZE)]
            if direction in ("right", "down"):
                line.reverse()
            new_line, points = self.collapse(line)
            gained += points
            if direction in ("right", "down"):
                new_line.reverse()
            if direction in ("left", "right"):
                updated[i] = new_line
            else:
                for r in range(SIZE):
                    updated[r][i] = new_line[r]

        if updated == self.board:
            return False

        self.previous = original
        self.board = updated
        self.score += gained
        self.moves += 1
        self.spawn()
        if any(value >= TARGET for row in self.board for value in row):
            self.won = True
        self.over = not self.can_move()
        return True

    def can_move(self):
        for r in range(SIZE):
            for c in range(SIZE):
                value = self.board[r][c]
                if value == 0:
                    return True
                if r + 1 < SIZE and self.board[r + 1][c] == value:
                    return True
                if c + 1 < SIZE and self.board[r][c + 1] == value:
                    return True
        return False

    def undo(self):
        if self.previous is None:
            return False
        state = self.previous
        self.previous = None
        self.load(state)
        return True

    def reset(self):
        self.board = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.moves = 0
        self.won = False
        self.over = False
        self.previous = None
        self.spawn()
        self.spawn()

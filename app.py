"""Brython browser interface for PyMerge. The game logic is in game.py."""

import json
from browser import document, window
from game import Game2048

SAVE_KEY = "pymerge-2048-game-v1"
BEST_KEY = "pymerge-2048-best-v1"
KEYS = {
    "ArrowUp": "up", "ArrowDown": "down", "ArrowLeft": "left", "ArrowRight": "right",
    "w": "up", "s": "down", "a": "left", "d": "right",
}

engine = Game2048(start=False)
best = 0
win_announced = False
swipe_start = None


def get_store(key):
    try:
        return window.localStorage.getItem(key)
    except Exception:
        return None


def set_store(key, value):
    try:
        window.localStorage.setItem(key, value)
    except Exception:
        pass


def load_saved():
    global best, win_announced
    try:
        best = max(0, int(get_store(BEST_KEY) or 0))
    except (ValueError, TypeError):
        best = 0
    try:
        raw = get_store(SAVE_KEY)
        if raw:
            engine.load(json.loads(raw))
        else:
            engine.reset()
    except Exception:
        engine.reset()
    best = max(best, engine.score)
    win_announced = engine.won


def save():
    set_store(SAVE_KEY, json.dumps(engine.snapshot()))
    set_store(BEST_KEY, str(best))


def maximum_tile():
    return max(value for row in engine.board for value in row)


def render():
    board_el = document["board"]
    board_el.innerHTML = ""
    for r, row in enumerate(engine.board):
        for c, value in enumerate(row):
            cell = document.createElement("div")
            css = f"tile tile-{value}" if value <= 2048 else "tile tile-super"
            if value:
                css += " tile-filled"
            cell.className = css
            cell.textContent = str(value) if value else ""
            cell.setAttribute("role", "gridcell")
            cell.setAttribute("aria-label", f"Row {r + 1}, column {c + 1}: {value or 'empty'}")
            board_el.appendChild(cell)

    document["score"].textContent = str(engine.score)
    document["best"].textContent = str(best)
    document["moves"].textContent = str(engine.moves)
    document["peak-tile"].textContent = str(maximum_tile())
    document["undo-btn"].disabled = engine.previous is None

    peak = maximum_tile()
    for value in (128, 256, 512, 1024, 2048):
        el = document[f"milestone-{value}"]
        if peak >= value:
            el.classList.add("completed")
        else:
            el.classList.remove("completed")

    progress = min(100, round(peak / 2048 * 100))
    document["progress-fill"].style.width = f"{progress}%"
    document["progress-text"].textContent = f"{progress}%"

    if engine.over:
        document["state-text"].textContent = "Game over · Try again?"
        document["state-led"].className = "status-dot status-over"
    elif engine.won:
        document["state-text"].textContent = "2048 reached · Legend!"
        document["state-led"].className = "status-dot status-won"
    else:
        document["state-text"].textContent = "Game in progress"
        document["state-led"].className = "status-dot"

    document["loading"].hidden = True


def show_modal(title, desc, continue_label="Keep playing", allow_continue=True):
    document["modal-title"].textContent = title
    document["modal-desc"].textContent = desc
    document["continue-btn"].textContent = continue_label
    document["continue-btn"].hidden = not allow_continue
    document["modal"].hidden = False


def close_modal(event=None):
    document["modal"].hidden = True
    document["board"].focus()


def check_status():
    global win_announced
    if engine.won and not win_announced:
        win_announced = True
        show_modal("You made it to 2048!", "The board is yours. Keep combining, or begin a fresh round.")
    elif engine.over:
        show_modal("No more moves!", "Every great run ends somewhere. Give it another shot.", allow_continue=False)


def do_move(direction):
    global best
    if not document["modal"].hidden:
        return
    if engine.move(direction):
        best = max(best, engine.score)
        save()
        render()
        check_status()


def on_key(event):
    key = event.key
    if key in ("Escape",) and not document["modal"].hidden and not engine.over:
        close_modal()
        return
    if event.ctrlKey and key.lower() == "z":
        event.preventDefault()
        on_undo()
        return
    direction = KEYS.get(key) or KEYS.get(key.lower())
    if direction:
        event.preventDefault()
        do_move(direction)


def on_reset(event=None):
    global win_announced
    engine.reset()
    win_announced = False
    document["modal"].hidden = True
    save()
    render()
    document["board"].focus()


def on_undo(event=None):
    global win_announced
    if engine.undo():
        win_announced = engine.won
        document["modal"].hidden = True
        save()
        render()
        document["board"].focus()


def on_touch_start(event):
    global swipe_start
    if event.touches.length:
        touch = event.touches[0]
        swipe_start = (touch.clientX, touch.clientY)


def on_touch_end(event):
    global swipe_start
    if swipe_start is None or not event.changedTouches.length:
        return
    touch = event.changedTouches[0]
    dx = touch.clientX - swipe_start[0]
    dy = touch.clientY - swipe_start[1]
    swipe_start = None
    if max(abs(dx), abs(dy)) < 28:
        return
    if abs(dx) > abs(dy):
        do_move("right" if dx > 0 else "left")
    else:
        do_move("down" if dy > 0 else "up")


load_saved()
document["new-btn"].bind("click", on_reset)
document["reset-modal-btn"].bind("click", on_reset)
document["undo-btn"].bind("click", on_undo)
document["continue-btn"].bind("click", close_modal)
document.bind("keydown", on_key)
document["board"].bind("touchstart", on_touch_start)
document["board"].bind("touchend", on_touch_end)
for direction in ("up", "left", "down", "right"):
    document[f"direction-{direction}"].bind("click", lambda event, d=direction: do_move(d))

render()

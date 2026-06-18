ctions.py

from directions import NORTH, SOUTH, EAST, WEST

# actions.py

from directions import NORTH, SOUTH, WEST, EAST

ARROW_TO_DIR = {
    "Up":    NORTH,
    "Down":  SOUTH,
    "Left":  WEST,
    "Right": EAST,
}

CHAR_TO_DIR = {
    "w": NORTH,
    "s": SOUTH,
    "a": WEST,
    "d": EAST,
}


def handle_game_key(game, event):
    """
    JÃ¡tÃ©kbeli input feldolgozÃ¡sa.
    game: Game pÃ©ldÃ¡ny
    event: tkinter event
    """

    # 1) nyilak
    dir_ = ARROW_TO_DIR.get(event.keysym)
    # 2) ha nem nyÃ­l, prÃ³bÃ¡ljuk WASD-kÃ©nt (case-insensitive)
    if dir_ is None:
        dir_ = CHAR_TO_DIR.get(event.keysym.lower())
    if dir_ is None:
        return

    # itt mÃ¡r van egy Dir objektumunk
    d = dir_.delta  # ha nÃ¡lad 'vector' vagy 'step', akkor azt hasznÃ¡ld
    nx = game.px + d.x
    ny = game.py + d.y

    # pÃ¡lyahatÃ¡r
    if not (0 <= ny < len(game.room.grid) and 0 <= nx < len(game.room.grid[0])):
        return

    target = game.room.grid[ny][nx]

    if target in ["floor", "baddy"]:
        if target == "baddy":
            game.room.remove_baddy(nx, ny)
        game.px, game.py = nx, ny
        game.draw_init()
        game.update_lighting_animation()
        if hasattr(game, "update_exit_state"):
            game.update_exit_state()


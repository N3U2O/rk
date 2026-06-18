class Room:
    def __init__(self, grid, torches=None, exits=None):
        self.grid = grid          # 2D lista: "wall", "floor", "baddy", ...
        self.torches = torches or []  # [(x, y), ...]
        self.exits = exits or []      # [(x, y), ...]

    # --- MÃ©ret, hatÃ¡rok ---
    def size(self):
        w = len(self.grid[0])
        h = len(self.grid)
        return w, h

    def in_bounds(self, x, y):
        w, h = self.size()
        return 0 <= x < w and 0 <= y < h

    # --- Tartalom lekÃ©rdezÃ©se ---
    def tile_at(self, x, y):
        return self.grid[y][x]

    def is_wall(self, x, y):
        return self.grid[y][x] == "wall"

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and not self.is_wall(x, y)

    def has_baddy(self, x, y):
        return self.grid[y][x] == "baddy"

    # --- MÃ³dosÃ­tÃ¡sok ---
    def remove_baddy(self, x, y):
        if self.has_baddy(x, y):
            self.grid[y][x] = "floor"
            return True
        return False

    def is_exit(self, x, y):
        return (x, y) in self.exits

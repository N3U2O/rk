from levels import Room
import random

class MapGenerator:
    def __init__(self, width=16, height=16):
        self.w = width
        self.h = height

    def generate(self, start_x, start_y):
        grid = [["0" for _ in range(self.w)] for _ in range(self.h)]
        cx, cy = start_x, start_y
        grid[cy][cx] = "1"
        floor_count = 1
        max_floors = int(self.w * self.h * 0.4)
        while floor_count < max_floors:
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            if 0 <= cx + dx < self.w and 0 <= cy + dy < self.h:
                cx += dx
                cy += dy
                if grid[cy][cx] == "0":
                    grid[cy][cx] = "1"
                    floor_count += 1
        for y in range(self.h):
            for x in range(self.w):
                if grid[y][x] == "0":
                    grid[y][x] = "wall"
                elif grid[y][x] == "1":
                    grid[y][x] = "floor"
        return grid

    def populate_extras(self, grid, start_x, start_y, world, wx, wy):
        torches = []
        exits = []
        grid[start_y][start_x] = "floor"
        exits.append((start_x, start_y))
        neighbor_offsets = [("e", 1, 0), ("w", -1, 0), ("n", 0, -1), ("s", 0, 1)]
        for direction, dx, dy in neighbor_offsets:
            neighbor_pos = (wx + dx, wy + dy)
            if neighbor_pos in world:
                neighbor_room = world[neighbor_pos]     # Room objektum
                neighbor_exits = neighbor_room.exits    # lista [(x,y), ...]
                for nx, ny in neighbor_exits:
                    if direction == "e" and nx == 0:
                        grid[ny][self.w - 1] = "floor"
                        exits.append((self.w - 1, ny))
                    elif direction == "w" and nx == self.w - 1:
                        grid[ny][0] = "floor"
                        exits.append((0, ny))
                    elif direction == "n" and ny == self.h - 1:
                        grid[0][nx] = "floor"
                        exits.append((nx, 0))
                    elif direction == "s" and ny == 0:
                        grid[self.h - 1][nx] = "floor"
                        exits.append((nx, self.h - 1))
        for y in range(self.h):
            for x in range(self.w):
                if grid[y][x] == "floor" and (x, y) != (start_x, start_y):
                    if random.random() < 0.05:
                        torches.append((x, y))
                elif grid[y][x] == "floor" and (x in [0, self.w - 1] or y in [0, self.h - 1]):
                    # Csak akkor engedjÃ¼nk random kijÃ¡ratot,
                    # ha a tÃºloldali world-cell mÃ¡r lÃ©tezik -> biztos van hovÃ¡ vezetnie.
                    if (x, y) not in exits:
                        if x == 0:
                            neighbor_pos = (wx - 1, wy)
                        elif x == self.w - 1:
                            neighbor_pos = (wx + 1, wy)
                        elif y == 0:
                            neighbor_pos = (wx, wy - 1)
                        else:  # y == self.h - 1
                            neighbor_pos = (wx, wy + 1)

                        if neighbor_pos in world and random.random() < 0.3:
                            exits.append((x, y))
        return {"grid": grid, "torches": torches, "exits": exits}

    def save_map(self, map_data, filename="lv02.map"):
        grid = map_data["grid"]
        torches = map_data["torches"]
        exits = map_data["exits"]
        to_char = {"wall": "0", "floor": "1", "baddy": "2"}
        with open(filename, "w") as f:
            for y in range(self.h):
                row_chars = []
                for x in range(self.w):
                    if (x, y) in torches:
                        row_chars.append("4")
                    elif (x, y) in exits:
                        row_chars.append("7")
                    else:
                        row_chars.append(to_char.get(grid[y][x], "1"))
                f.write("".join(row_chars) + "\n")

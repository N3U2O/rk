import os
import glob
import tkinter
from tkinter import messagebox
from mapgen import MapGenerator as Gen, Room
from effects import noise2d, FogLayer

class Sprite:
    """Alap osztály minden mozgó vagy álló tárgynak a pályán."""
    def __init__(self, canvas, x, y, image, tile_size):
        self.canvas = canvas
        self.tile_size = tile_size
        self.id = canvas.create_image(
            x * tile_size, y * tile_size,
            anchor="nw", image=image
        )

    def move_to(self, x, y):
        self.canvas.coords(self.id, x * self.tile_size, y * self.tile_size)

class AnimatedSprite(Sprite):
    """Fáklyákhoz: váltogatja a képeket megadott időközönként."""
    def __init__(self, canvas, x, y, images, tile_size):
        super().__init__(canvas, x, y, images[0], tile_size)
        self.images = images
        self.frame = 0
        self.animate()

    def animate(self):
        self.frame = (self.frame + 1) % len(self.images)
        self.canvas.itemconfig(self.id, image=self.images[self.frame])
        # 500 ms múlva újra meghívja magát (animációs sebesség)
        self.canvas.after(500, self.animate)

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("TkGame - Main Menu")
        self.root.geometry("320x200")
        tkinter.Label(root, text="TkGame", font=("Arial", 16, "bold")).pack(pady=20)
        tkinter.Button(root, text="New game", width=20, command=self.new_game).pack(pady=10)
        self.btn_load = tkinter.Button(root, text="Continue last game", width=20, command=self.last_game)
        if not os.path.exists("savegame.txt"):
            self.btn_load.config(state="disabled")
        self.btn_load.pack(pady=10)
        self.root.bind("<KeyPress-N>", lambda e: self.new_game())

    def new_game(self):
        self.root.destroy()
        new_root = tkinter.Tk()
        new_root.title("TkGame")
        app = Game(new_root, mode="new", map_file="lv01.map")
        new_root.mainloop()

    def last_game(self):
        self.root.destroy()
        new_root = tkinter.Tk()
        new_root.title("TkGame")
        app = Game(new_root, mode="load", map_file="savegame.txt")
        new_root.mainloop()

class Game:
    def __init__(self, root, mode="new", map_file="lv01.map"):
        self.root = root
        self.tile_size = 32
        self.light_radius = 4 # Fény sugara (blokkban)
        
        # Képek betöltése
        self.tiledesc = ["wall", "floor", "baddy", "player",
                         "torch1", "torch2", "arrowe", "arrown",
                         "arrows", "arroww", "arrowv"]
        self.im = {desc: tkinter.PhotoImage(file=f"{n}.png")
                   for n, desc in enumerate(self.tiledesc[:6])}
        self.im.update({desc: tkinter.PhotoImage(file=f"7_{desc[-1]}.png")
                        for desc in self.tiledesc[6:]})
        print(self.im)
 
        self.room = None
        self.world = {} # (wx, wy) -> Room
        self.wx, self.wy = 0, 0
        self.px, self.py = 0, 0
        self.exit_direction = None   # melyik irányba lehet innen továbblépni
        self.exit_hint_id = None     # HUD szöveg id-ja
        if mode == "new":
            self.load_initial_map(map_file)
        elif mode == "load":
            self.load(map_file)
        w,h=len(self.room.grid[0]), len(self.room.grid)
        self.canvas = tkinter.Canvas(
            root, width=w*self.tile_size, height=h*self.tile_size,
            bg="black", highlightthickness=0
        )
        self.canvas.pack()
        
        self.draw_init()
        self.fog = FogLayer(self.canvas, w, h, tile_size=self.tile_size, fog_cell=16)
        self.fog.build()
        self.noise_time = 0.0
        self.light_anim_interval = 300  # ms
        self.update_lighting_animation()

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<KeyPress>", self.handle_key)
        self.root.bind("<KeyPress-S>", lambda e: self.save_with_check())

    def load_initial_map(self, filename):
        grid = []
        torches = []
        exits = []

        with open(filename, "r") as f:
            for y, line in enumerate(f.readlines()):
                row = []
                for x, char in enumerate(line.strip()):
                    if char == '@':
                        self.px, self.py = x, y
                        row.append("floor")
                    elif char == '4':
                        torches.append((x, y))
                        row.append("wall")
                    elif char == '2':
                        row.append("baddy")
                    elif char in '<^v>xX':
                        exits.append((x,y))
                        row.append("floor")
                    elif char in '.,':
                        row.append("floor")
                    else:
                        row.append(self.tiledesc[int(char)])
                grid.append(row)
        self.room = Room(grid, torches=torches, exits=exits)
        self.world[(self.wx, self.wy)] = self.room

    def load(self, filename):
        with open(filename, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        self.world = {}
        self.room = None
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line == "[PLAYER]":
                self.wx, self.wy, self.px, self.py = map(int, lines[idx + 1].split(","))
                idx += 2
            elif line.startswith("[ROOM_"):
                coords = tuple(map(int, line[6:-1].split("_")))
                idx += 1
                grid = []
                torches = []
                exits = []
                # Feltételezzük, hogy 16 sor van – ha később változik a méret, érdemes lesz
                # inkább a következő [ROOM_] vagy [PLAYER] tagig olvasni.
                for y in range(16):
                    row_chars = lines[idx]
                    row_tiles = []
                    for x, char in enumerate(row_chars):
                        if char == '4':
                            torches.append((x, y))
                            row_tiles.append("wall")   # fáklya a falon
                        elif char == 'x':
                            exits.append((x, y))
                            row_tiles.append("floor")  # kijárat padlón
                        elif char == '2':
                            row_tiles.append("baddy")
                        else:                          # 0 -> wall, bármi más -> floor
                            row_tiles.append("wall" if char == '0' else "floor")
                    grid.append(row_tiles)
                    idx += 1
                self.world[coords] = Room(grid, torches=torches, exits=exits)
            else:       # Biztonság kedvéért: ha valami ismeretlen sor, menjünk tovább
                idx += 1
        self.room = self.world[(self.wx, self.wy)]

    def _get_next_old_filename(self):
        counter = 0
        while True:
            filename = f"SAVE{counter:04d}.old"
            if not os.path.exists(filename):
                return filename
            counter += 1

    def save_with_check(self):
        filename = "savegame.txt"
        if os.path.exists(filename):
            resp = messagebox.askyesno("Confirm save", "savegame.txt already exists. Overwrite?")
            if not resp:
                print("Aborted save.")
                return
            old_name = self._get_next_old_filename()
            try:
                os.rename(filename, old_name)
                print(f"Backup {old_name} created.")
            except Exception as e:
                print(f"Failed to create backup: {e}")
                return
        self.execute_save(filename)

    def execute_save(self, filename):
        # 1. Az aktuális room-ot is tegyük be a world-be
        self.world[(self.wx, self.wy)] = self.room

        to_char = {"wall": '0', "floor": '1', "baddy": '2'}

        with open(filename, "w") as f:
            # PLAYER blokk
            f.write("[PLAYER]\n")
            f.write(f"{self.wx},{self.wy},{self.px},{self.py}\n\n")

            # ROOM blokkok
            for (wx, wy), room in self.world.items():
                f.write(f"[ROOM_{wx}_{wy}]\n")
                for y, row in enumerate(room.grid):
                    line_chars = []
                    for x, tile in enumerate(row):
                        if (x, y) in room.torches:
                            line_chars.append("4")
                        elif (x, y) in room.exits:
                            line_chars.append("x")
                        else:
                            line_chars.append(to_char.get(tile, '1'))
                    f.write("".join(line_chars) + "\n")
                f.write("\n")

        print("Succesful save.")

    def _get_exit_orientation(self, x, y):
        max_y = len(self.room.grid) - 1
        max_x = len(self.room.grid[0]) - 1
        if x == 0:     return "w"
        if y == 0:     return "n"
        if x == max_x: return "e"
        if y == max_y: return "s"
        return "v"

    def draw_init(self):
        # 1. Alapréteg: Padló és falak
        for y, row in enumerate(self.room.grid):
            for x, tile in enumerate(row):
                if tile != "wall":
                    self.canvas.create_image(x*32, y*32, anchor="nw", image=self.im["floor"])
                if tile in ["0", "wall", "baddy"]:
                    if tile == "0":
                        self.room.grid[y][x] = "wall"
                    tag = f"tile_{x}_{y}"
                    self.canvas.create_image(x*32, y*32, anchor="nw", image=self.im[tile], tags=tag)

        # 2. Fáklyák
        for tx, ty in self.room.torches:
            AnimatedSprite(self.canvas, tx, ty, [self.im["torch1"], self.im["torch2"]], 32)

        # 3. Játékos
        self.hero = Sprite(self.canvas, self.px, self.py, self.im["player"], 32)

        # 4. Kijáratok
        for ex, ey in self.room.exits:
            orientation = self._get_exit_orientation(ex, ey)
            Sprite(self.canvas, ex, ey, self.im[f"arrow{orientation}"], 32)

        self.update_lighting()
        self.canvas.tag_raise(self.hero.id)

    def update_lighting(self):
        if not hasattr(self, "fog"):
            return

        # Fényforrások: játékos + fáklyák
        sources = [(self.px, self.py)] + self.room.torches

        base_r = self.light_radius
        amplitude = 1.7  # mennyire fodrozzon

        self.fog.update(
            sources=sources,
            base_radius_tiles=self.light_radius,
            t=self.noise_time,
            noise_func=noise2d,
            amplitude=.7,
            scale=2,
            speed=.1,
            seed=42
        )

    def update_lighting_animation(self):
        self.noise_time += 0.02
        self.update_lighting()
        self.root.after(self.light_anim_interval, self.update_lighting_animation)

    def show_passage_hint(self, direction):
        """Kis HUD-üzenet a kijáratról, középen, háttér nélkül."""
        self.clear_passage_hint()

        dir_hu = {
            "n": "észak",
            "s": "dél",
            "e": "kelet",
            "w": "nyugat",
        }.get(direction, "ismeretlen irány")

        text = f"Tovább mehetsz {dir_hu} felé.\nNyomj még egyet ugyanabba az irányba!"

        width = int(self.canvas["width"])
        height = int(self.canvas["height"])

        self.exit_hint_id = self.canvas.create_text(
            width // 2,
            height // 2,
            text=text,
            fill="white",
            font=("Arial", 11, "bold"),
            justify="center"
        )

        self.canvas.tag_raise(self.exit_hint_id)
        if hasattr(self, "hero"):
            self.canvas.tag_raise(self.hero.id)

    def clear_passage_hint(self):
        if self.exit_hint_id is not None:
            self.canvas.delete(self.exit_hint_id)
            self.exit_hint_id = None

    def update_exit_state(self):
        """Eldönti, hogy kijáraton állsz-e, és ennek megfelelően állítja az
        exit_direction-t + HUD-ot."""
        if self.room.is_exit(self.px, self.py):
            direction = self._get_exit_orientation(self.px, self.py)
            self.exit_direction = direction
            self.show_passage_hint(direction)
        else:
            self.exit_direction = None
            self.clear_passage_hint()

    def handle_key(self, event):
        moves = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
        moves["w"] = moves["W"] = moves["Up"]
        moves["s"] = moves["S"] = moves["Down"]
        moves["a"] = moves["A"] = moves["Left"]
        moves["d"] = moves["D"] = moves["Right"]

        if event.keysym not in moves:
            return

        dx, dy = moves[event.keysym]
        nx, ny = self.px + dx, self.py + dy

        # billentyű -> irány kód
        key_to_dir = {
            "Up": "n", "w": "n", "W": "n",
            "Down": "s", "s": "s", "S": "s",
            "Left": "w", "a": "w", "A": "w",
            "Right": "e", "d": "e", "D": "e",
        }
        pressed_dir = key_to_dir[event.keysym]

        # 1) Ha már állunk kijáraton, és ugyanabba az irányba nyomunk, akkor LÉPJÜNK ÁT
        if self.exit_direction is not None and pressed_dir == self.exit_direction:
            self.clear_passage_hint()
            self.exit_direction = None
            self.root.after(100, self.change_level)
            return

        # 2) Egyébként normál mozgás
        if self.room.is_walkable(nx, ny):
            self.px, self.py = nx, ny
            if self.room.remove_baddy(nx, ny):
                self.canvas.delete(f"tile_{nx}_{ny}")
            self.hero.move_to(self.px, self.py)
            # frissítsük, hogy kijáraton állunk-e
            self.update_exit_state()
            self.update_lighting()
        else:
            # falnak mentünk: ha korábban kijáraton álltunk, de NEM a kijárat irányába nyomtunk,
            # akkor töröljük a kijárati állapotot, mert elutasítottuk az ajánlatot
            if self.exit_direction is not None:
                self.exit_direction = None
                self.clear_passage_hint()

    def change_level(self):
        self.clear_passage_hint()
        self.exit_direction = None

        direction = self._get_exit_orientation(self.px, self.py)

        # Elmentjük a jelenlegi pályát
        self.world[(self.wx, self.wy)] = self.room

        # világ-koordináta frissítése
        target_wx, target_wy = self.wx, self.wy
        if direction == "e": target_wx += 1
        elif direction == "w": target_wx -= 1
        elif direction == "s": target_wy += 1
        elif direction == "n": target_wy -= 1

        # ha még sosem jártunk ott, akkor generálni fogunk,
        # de csak akkor engedjük, ha a generálás ad értelmes bejáratot
        # (erre mindjárt visszatérünk)

        # 2. Új bejárati pont kiszámítása
        new_sx = 0 if direction == "e" else 15 if direction == "w" else self.px
        new_sy = 0 if direction == "s" else 15 if direction == "n" else self.py

        # ha cél-szoba már létezik, és a bejárati pont NEM walkable, akkor ne váltsunk
        if (target_wx, target_wy) in self.world:
            target_room = self.world[(target_wx, target_wy)]
            if not target_room.is_walkable(new_sx, new_sy):
                # csapda-kijárat: kezeljük sima padlóként
                # visszaállítjuk a világ-koordinátát és kilépünk
                self.wx, self.wy = self.wx, self.wy
                return

        # innentől mehet az eredeti logika, csak self.wx/self.wy-t a target-re állítjuk:
        self.wx, self.wy = target_wx, target_wy

        if (self.wx, self.wy) in self.world:
            self.room = self.world[(self.wx, self.wy)]
        else:
            gen = Gen(width=len(self.room.grid[0]), height=len(self.room.grid))
            raw_grid = gen.generate(new_sx, new_sy)
            data = gen.populate_extras(raw_grid, new_sx, new_sy,
                                       self.world, self.wx, self.wy)
            self.room = Room(data["grid"], torches=data["torches"], exits=data["exits"])

        self.canvas.delete("all")
        self.px, self.py = new_sx, new_sy
        self.draw_init()       # ÚJ: fogréteg újraépítése az új roomhoz
        w, h = len(self.room.grid[0]), len(self.room.grid)
        # ha már létezett fog, ne hagyjuk a régi cells dict-et
        if hasattr(self, "fog"):
            self.fog = FogLayer(self.canvas, w, h,
                                tile_size=self.tile_size,
                                fog_cell=self.fog.fog_cell)
        else:
            self.fog = FogLayer(self.canvas, w, h,
                                tile_size=self.tile_size,
                                fog_cell=16)  # vagy amit használsz
        self.fog.build()

if __name__ == "__main__":
    menu_root = tkinter.Tk()
    menu = MainMenu(menu_root)
    menu_root.mainloop()


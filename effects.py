# effects.py

def hash2(x, y, seed=0):
    n = (x * 73856093) ^ (y * 19349663) ^ seed
    n = n & 0xffffffff
    return n / 0xffffffff

def smooth_noise2(x, y, seed=0):
    s = 0.0
    count = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            s += hash2(x + dx, y + dy, seed)
            count += 1
    return s / count

def noise2d(x, y, t=0.0, scale=0.5, speed=0.1, seed=0):
    fx = int(x * scale + t * speed)
    fy = int(y * scale + t * speed)
    v = smooth_noise2(fx, fy, seed)
    return 2.0 * v - 1.0  # -1..1

class FogLayer:
    """
    Finomabb fog-of-war réteg.
    Egy 32x32-es tile fölé (tile_size) fog_scale*fog_scale darab fog cellát rajzol.
    Alap: fog_cell = 8 -> fog_scale = 4 -> 8x8-as kis négyzetek.
    """

    def __init__(self, canvas, room_width, room_height,
                 tile_size=32, fog_cell=8):
        self.canvas = canvas
        self.tile_size = tile_size
        self.fog_cell = fog_cell
        self.fog_scale = tile_size // fog_cell  # pl. 32 // 8 = 4
        self.room_width = room_width   # tile-ben
        self.room_height = room_height # tile-ben

        # fog rács mérete finom gridben
        self.fog_width = room_width * self.fog_scale
        self.fog_height = room_height * self.fog_scale

        # (fx, fy) -> canvas id
        self.cells = {}

    def build(self):
        """Létrehozza az összes kis ködcella téglalapot."""
        self.cells.clear()
        for fy in range(self.fog_height):
            for fx in range(self.fog_width):
                # pixel koordináták
                x0 = fx * self.fog_cell
                y0 = fy * self.fog_cell
                x1 = x0 + self.fog_cell
                y1 = y0 + self.fog_cell

                cid = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill="black", outline=""
                )

                self.cells[(fx, fy)] = cid

    def hide_all(self):
        """Minden ködcella látható (sötét)."""
        for cid in self.cells.values():
            self.canvas.itemconfig(cid, state='normal')

    def update(self, sources, base_radius_tiles,
               t, noise_func=noise2d,
               amplitude=0.7, scale=0.5, speed=0.1, seed=42):
        """
        sources: lista tile-koordinátákról [(sx,sy), ...]
        base_radius_tiles: tile-ben mért sugár (pl. 5)
        t: idő (Game.noise_time)
        """
        if not self.cells:
            return

        # először mindent sötétre
        self.hide_all()

        # sugár fog-rácsban (tile -> fogcell)
        base_r_fog = base_radius_tiles * self.fog_scale

        for (sx_tile, sy_tile) in sources:
            # forrás középpontjának fog-koordinátája
            cx = sx_tile * self.fog_scale + self.fog_scale // 2
            cy = sy_tile * self.fog_scale + self.fog_scale // 2

            # körülötte vizsgáljuk a fog cellákat
            r = base_r_fog
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    fx = cx + dx
                    fy = cy + dy
                    if (fx, fy) not in self.cells:
                        continue

                    dist2 = dx*dx + dy*dy

                    # zaj a finom rácson
                    n = noise_func(
                        fx, fy, t=t,
                        scale=scale, speed=speed, seed=seed
                    )
                    eff_r = base_r_fog + int(amplitude * self.fog_scale * n)

                    if dist2 <= eff_r * eff_r:
                        self.canvas.itemconfig(
                            self.cells[(fx, fy)], state='hidden'
                        )

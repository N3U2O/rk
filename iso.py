def generate_checkerboard(width, height):
    """Generates a 2D grid filled with a checkerboard pattern ('#' and '.')."""
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            # Alternate characters based on coordinates
            if (x + y) % 2 == 0:
                row.append("#")
            else:
                row.append(".")
        grid.append(row)
    return grid


def render_isometric(source_grid):
    src_height = len(source_grid)
    src_width = len(source_grid[0]) if src_height > 0 else 0

    # Calculate bounding box for the output screen
    # Transforming corners: (0,0), (W,0), (0,H), (W,H)
    # iso_x ranges from -src_height to +src_width
    # iso_y ranges from 0 to (src_width + src_height) // 2
    
    offset_x = src_height * 2  # Shift right to keep coordinates positive
    screen_width = (src_width + src_height) * 2 + 4
    screen_height = (src_width + src_height) + 2

    # Initialize a blank screen buffer with spaces
    screen = [[" " for _ in range(screen_width)] for _ in range(screen_height)]

    # Project each tile from the top view to the isometric view
    for y in range(src_height):
        for x in range(src_width):
            char = source_grid[y][x]

            # Isometric projection formulas adjusted for text aspect ratio
            iso_x = (x - y) * 2 + offset_x
            iso_y = (x + y) // 2

            # Basic bounds safety check
            if 0 <= iso_x < screen_width and 0 <= iso_y < screen_height:
                screen[iso_y][iso_x] = char
                
                # Optional: Make the "tiles" wider so they look more connected
                if iso_x + 1 < screen_width:
                    screen[iso_y][iso_x + 1] = char

    # Print the screen buffer
    for row in screen:
        print("".join(row))


# --- Execution ---
if __name__ == "__main__":
    # 1. Define the size of our top-down checkerboard
    board_width = 8
    board_height = 8

    print("--- 2D Top View Grid ---")
    top_view = generate_checkerboard(board_width, board_height)
    for row in top_view:
        print(" ".join(row))

    print("\n--- Projected 3D Isometric View ---")
    render_isometric(top_view)


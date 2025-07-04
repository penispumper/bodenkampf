import pygame

def load_strip(filename, cols, rows, frame_width, frame_height):
    """
    Load a sprite sheet and split it into a list of frames.
    cols, rows: how many columns/rows of frames
    frame_width, frame_height: size of each frame in px
    """
    sheet = pygame.image.load(filename).convert_alpha()
    frames = []
    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(col * frame_width, row * frame_height,
                               frame_width, frame_height)
            image = sheet.subsurface(rect)
            frames.append(image)
    return frames

# Example: if walk is in the first row (6 cols × 1 row, 64×64)
walk_frames = load_strip("sprites/player/walk.png", cols=3, rows=2, frame_width=64, frame_height=64)


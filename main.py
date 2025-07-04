import pygame
import sys
import os


# --- Konfiguration ---
WIDTH, HEIGHT = 800, 480
FPS = 60
GROUND_Y = HEIGHT - 60

# Physik
GRAVITY = 0.5
JUMP_SPEED = -10

# Spieler-Parameter
PLAYER_WIDTH, PLAYER_HEIGHT = int(40 * 1.3), int(60 * 1.4)
PLAYER_SPEED = 5
CROUCH_FACTOR = 0.5  # halb so hoch beim Ducken

# Level-Parameter
NUM_LEVELS = 5
SCREENS_PER_LEVEL = 3
LEVEL_WIDTH = WIDTH * SCREENS_PER_LEVEL

# Gegner-Parameter
ENEMY_WIDTH, ENEMY_HEIGHT = int(40 * 1.3), int(60 * 1.4)

# Farben
BG_COLOR       = (50, 150, 200)
GROUND_COLOR   = (100, 50, 0)
OBSTACLE_COLOR = (150, 75, 0)
WATER_COLOR    = (255, 255, 0)
TEXT_COLOR     = (255, 255, 255)

# Pygame initialisieren
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Street‐Mario mit Sprite")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# Sprite laden (full image)
try:
    raw_image = pygame.image.load('sprite_enemy.png').convert_alpha()
    enemy_image = pygame.transform.scale(raw_image, (ENEMY_WIDTH, ENEMY_HEIGHT))
    print("sprite_enemy.png erfolgreich geladen!")
except Exception as e:
    print(f"Warnung: sprite_enemy.png konnte nicht geladen werden: {e}")
    enemy_image = None

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

# --- load player animations ---
def load_frames(prefix):
    path = os.path.join("sprites", f"player/{prefix}.png")
    original_frames = load_strip(path, cols=3, rows=2, frame_width=166, frame_height=250)

    # Scale proportionally (uniform scaling factor):
    scale_factor = 1  # adjust this number as needed
    scaled_width = int(64 * scale_factor)
    scaled_height = int(64 * scale_factor)

    transformed_frames = []
    for frame in original_frames:
        transformed_frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
        transformed_frames.append(transformed_frame)

    return transformed_frames

walk_frames_r   = load_frames("walk-removebg-preview")
walk_frames_l   = [pygame.transform.flip(f, True, False) for f in walk_frames_r]
jump_frames_r   = load_frames("jump")
jump_frames_l   = [pygame.transform.flip(f, True, False) for f in jump_frames_r]
crouch_frames_r = load_frames("crouch")
crouch_frames_l = [pygame.transform.flip(f, True, False) for f in crouch_frames_r]

# Animation state
anim_state = "idle"   # "idle","walk","jump","crouch"
anim_timer = 0        # last update time
anim_frame = 0

def show_intro():
    intro = [
        "Es ist ein ganz normaler Morgen an der Universität.",
        "Leon macht sich auf den Weg…",
        "Drücke [Leertaste], um zu starten..."
    ]
    screen.fill(BG_COLOR)
    for i, line in enumerate(intro):
        text = font.render(line, True, TEXT_COLOR)
        x = WIDTH//2 - text.get_width()//2
        y = 60 + i*30
        screen.blit(text, (x, y))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False
        clock.tick(FPS)

def spawn_enemy():
    x = WIDTH*(SCREENS_PER_LEVEL-1) + WIDTH//2 - ENEMY_WIDTH//2
    y = GROUND_Y - ENEMY_HEIGHT
    return pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)

def create_obstacles():
    obs = []
    # Bildschirm 1
    obs.append({'rect': pygame.Rect(150, GROUND_Y-10, 100, 10), 'type': 'spike'})
    obs.append({'rect': pygame.Rect(350, GROUND_Y-20, 40, 20),  'type': 'spring'})
    obs.append({'rect': pygame.Rect(550, GROUND_Y-120, 80, 20),'type': 'platform'})
    obs.append({'rect': pygame.Rect(480, GROUND_Y-5, 200, 10),  'type': 'water'})
    # Bildschirm 2
    off = WIDTH
    obs.append({'rect': pygame.Rect(off+150, GROUND_Y-20, 40, 20),  'type': 'spring'})
    obs.append({'rect': pygame.Rect(off+200, GROUND_Y-10, 120, 10), 'type': 'spike'})
    obs.append({'rect': pygame.Rect(off+600, GROUND_Y-60, 60, 60),  'type': 'rotating'})
    return obs

# Intro
show_intro()

# Spielzustände
level = 1
in_battle = False
enemy_alive = True

# Spieler initialisieren
player = pygame.Rect(-PLAYER_WIDTH, GROUND_Y-PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT)
player_vel_y = 0

# Gegner und Hindernisse
enemy = spawn_enemy()
obstacles = create_obstacles() if level == 1 else []

# Hauptschleife
running = True
while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    # Events
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if in_battle and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_f:
                enemy_alive = False; in_battle = False
            if e.key == pygame.K_r:
                player.x = -PLAYER_WIDTH; in_battle = False
        if not in_battle and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE and player_vel_y == 0:
                player_vel_y = JUMP_SPEED

    keys = pygame.key.get_pressed()
    old_x, old_y = player.x, player.y

    if not in_battle:
        # Bewegung
        if keys[pygame.K_LEFT]:
            player.x = max(-PLAYER_WIDTH, player.x - PLAYER_SPEED)
        if keys[pygame.K_RIGHT]:
            player.x += PLAYER_SPEED

        # horizontale Kollision
        for o in obstacles:
            r = o['rect']
            if player.colliderect(r):
                if o['type']=='spike':
                    player.x = -PLAYER_WIDTH; player_vel_y = 0
                    break
                if old_x < player.x:
                    player.x = r.x - PLAYER_WIDTH
                else:
                    player.x = r.x + r.width

        # Gravitation
        player_vel_y += GRAVITY
        player.y += player_vel_y

        # vertikale Kollision/Effekte
        for o in obstacles:
            r, t = o['rect'], o['type']
            if player.colliderect(r):
                if t == 'spike':
                    player.x = -PLAYER_WIDTH; player_vel_y = 0; break
                if t == 'spring':
                    player_vel_y = JUMP_SPEED * 1.5
                    player.bottom = r.top
                if t == 'platform' and old_y + PLAYER_HEIGHT <= r.top:
                    player.bottom = r.top
                    player_vel_y = 0
                if t == 'water':
                    player.x -= PLAYER_SPEED * 0.5
                if t == 'rotating':
                    player.x -= PLAYER_SPEED * 2

        # Boden
        if player.y >= GROUND_Y - PLAYER_HEIGHT:
            player.y = GROUND_Y - PLAYER_HEIGHT
            player_vel_y = 0

        # Encounter
        if enemy_alive and player.colliderect(enemy):
            in_battle = True

    # Kamera so, dass sie auf die Mitte des Spielers zielt
    cam_x = max(0, min(
        player.x + PLAYER_WIDTH//2 - WIDTH//2,
        LEVEL_WIDTH - WIDTH
    ))
    # Levelwechsel
    if not enemy_alive and player.x >= LEVEL_WIDTH:
        level += 1
        if level > NUM_LEVELS:
            break
        # Transition
        screen.fill(BG_COLOR)
        txt = font.render(f"Level {level}", True, TEXT_COLOR)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2,
                          HEIGHT//2 - txt.get_height()//2))
        pygame.display.flip()
        pygame.time.wait(2000)

        enemy_alive = True
        enemy = spawn_enemy()
        player.x, player.y = -PLAYER_WIDTH, GROUND_Y - PLAYER_HEIGHT
        player_vel_y = 0
        obstacles = create_obstacles()

    # Zeichnen
    screen.fill(BG_COLOR)
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    for o in obstacles:
        r = o['rect']
        col = WATER_COLOR if o['type']=='water' else OBSTACLE_COLOR
        pygame.draw.rect(screen, col, (r.x - cam_x, r.y, r.width, r.height))

    # Gegner
    if enemy_alive:
        ex, ey = enemy.x - cam_x, enemy.y
        if enemy_image:
            screen.blit(enemy_image, (ex, ey))
        else:
            pygame.draw.rect(screen, (50,200,50),
                             (ex, ey, ENEMY_WIDTH, ENEMY_HEIGHT))

    # ——— Player Animation ———
    # Bestimme Zustand
    if player_vel_y != 0:
        state = "jump"
    elif keys[pygame.K_DOWN] and player_vel_y == 0:
        state = "crouch"
    elif keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
        state = "walk"
    else:
        state = "idle"

    # Wähle Frames
    facing = "l" if keys[pygame.K_LEFT] else "r"
    if state == "walk":
        frames = walk_frames_l if facing=="l" else walk_frames_r
    elif state == "jump":
        frames = jump_frames_l if facing=="l" else jump_frames_r
    elif state == "crouch":
        frames = crouch_frames_l if facing=="l" else crouch_frames_r
    else:
        # idle: erstes Walk-Frame
        frames = [walk_frames_l[0]] if facing=="l" else [walk_frames_r[0]]

    # Frame-Advance alle 100 ms
    if anim_state != state:
        anim_state = state
        anim_frame = 0
        anim_timer = now
    elif now - anim_timer > 100:
        anim_timer = now
        anim_frame = (anim_frame + 1) % len(frames)

    current_image = frames[anim_frame]

    # Crouch-Skalierung
    if state == "crouch":
        new_h = int(PLAYER_HEIGHT * CROUCH_FACTOR)
        current_image = pygame.transform.scale(current_image, (PLAYER_WIDTH, new_h))
        py = GROUND_Y - new_h
    else:
        py = player.y

    screen.blit(current_image, (player.x - cam_x, py))

    # UI
    info = font.render(
        f"Level {level}/{NUM_LEVELS}  Screen {cam_x//WIDTH+1}/{SCREENS_PER_LEVEL}",
        True, TEXT_COLOR
    )
    screen.blit(info, (10, 10))
    fps = font.render(f"FPS: {int(clock.get_fps())}", True, TEXT_COLOR)
    screen.blit(fps, (WIDTH-100, 10))

    # Battle
    if in_battle:
        l1 = font.render(f"Level {level}: Gegner blockiert!", True, TEXT_COLOR)
        l2 = font.render("[F] kämpfen  [R] fliehen", True, TEXT_COLOR)
        screen.blit(l1, (50, 150))
        screen.blit(l2, (50, 180))

    pygame.display.flip()

pygame.quit()
sys.exit()

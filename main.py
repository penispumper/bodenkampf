import pygame
import sys
import os
import glob

# --- Config ---
WIDTH, HEIGHT = 800, 480
FPS = 60
GROUND_Y = HEIGHT - 60

GRAVITY = 0.5
JUMP_SPEED = -10

PLAYER_WIDTH, PLAYER_HEIGHT = int(40 * 1.3), int(60 * 1.4)
PLAYER_SPEED = 5
CROUCH_FACTOR = 0.5

SCREENS_PER_LEVEL = 3
LEVEL_WIDTH = WIDTH * SCREENS_PER_LEVEL

ENEMY_WIDTH, ENEMY_HEIGHT = int(50 * 1.3), int(70 * 1.4)

BG_COLOR       = (50, 150, 200)
GROUND_COLOR   = (100, 50, 0)
OBSTACLE_COLOR = (150, 75, 0)
WATER_COLOR    = (255, 255, 0)
TEXT_COLOR     = (255, 255, 255)

# --- Obstacle Image Registry ---
OBSTACLE_TYPES = {
    "spike":     {"img": "./sprites/obstacle/papertowel.png",     "color": (150, 150, 0)},
    "spring":    {"img": "sprites/map/spring.png",    "color": (120, 200, 120)},
    "platform":  {"img": "sprites/map/platform.png",  "color": (80, 80, 80)},
    "water":     {"img": "sprites/map/water.png",     "color": (100, 200, 255)},
    "rotating":  {"img": "sprites/map/rotating.png",  "color": (120, 120, 200)},
    # add more as needed
}

def load_obstacle_images():
    images = {}
    for typ, entry in OBSTACLE_TYPES.items():
        path = entry.get("img")
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                images[typ] = img
            except Exception:
                images[typ] = None
        else:
            images[typ] = None
    return images

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Street‐Mario mit Sprite")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

OBSTACLE_IMAGES = load_obstacle_images()

def load_image_safe(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        print(f"{path} erfolgreich geladen!")
        return img
    except Exception as e:
        print(f"Warnung: {path} konnte nicht geladen werden: {e}")
        return None

enemy_image = load_image_safe('sprite_enemy.png', (ENEMY_WIDTH, ENEMY_HEIGHT))
cloud_img_big = load_image_safe('./sprites/map/cloud.png', (120, 60))
cloud_img_small = pygame.transform.scale(cloud_img_big, (60, 30)) if cloud_img_big else None

bg_image2 = load_image_safe('./sprites/map/forest.png', (WIDTH, HEIGHT))  # Optional
bg_image3 = load_image_safe('./sprites/map/mountain.png', (WIDTH, HEIGHT)) # Optional

# --- Animation frame loaders ---
def load_animation_frames(folder, prefix, num_frames):
    """Load frames like folder/prefix1.png ... folder/prefixN.png"""
    frames = []
    for i in range(1, num_frames + 1):
        fname = os.path.join(folder, f"{prefix}{i}.png")
        if not os.path.exists(fname):
            raise Exception(f"Missing file: {fname}")
        img = pygame.image.load(fname).convert_alpha()
        img = pygame.transform.scale(img, (PLAYER_WIDTH, PLAYER_HEIGHT))
        frames.append(img)
    return frames

# Walk, Jump, Crouch Animation (6/6/1 frames each)
walk_frames_r = load_animation_frames("sprites/player/walk", "walk", 6)
walk_frames_l = [pygame.transform.flip(f, True, False) for f in walk_frames_r]
jump_frames_r = load_animation_frames("sprites/player/jump", "jump", 6)
jump_frames_l = [pygame.transform.flip(f, True, False) for f in jump_frames_r]
crouch_frames_r =  load_animation_frames("sprites/player/crouch", "crouch", 1)
crouch_frames_l = [pygame.transform.flip(f, True, False) for f in crouch_frames_r]

# --- Fight Animation Frames ---
def load_fight_frames(folder, prefix, num_frames):
    frames = []
    for i in range(1, num_frames + 1):
        fname = os.path.join(folder, f"{prefix}{i}.png")
        if not os.path.exists(fname):
            raise Exception(f"Missing fight file: {fname}")
        img = pygame.image.load(fname).convert_alpha()
        img = pygame.transform.scale(img, (PLAYER_WIDTH*2, PLAYER_HEIGHT*2))
        frames.append(img)
    return frames

fight_frames = load_fight_frames("sprites/fight", "fight", 3)

# --- Classes for modular levels ---
class Level:
    def __init__(self, background_draw_func, obstacle_factory, boss_factory=None, clouds=None):
        self.background_draw_func = background_draw_func
        self.obstacle_factory = obstacle_factory
        self.boss_factory = boss_factory or (lambda: None)
        self.clouds = clouds


def load_background_images(folder):
    images = []
    paths = sorted(glob.glob(os.path.join(folder, "*.png")))
    for path in paths:
        try:
            img = pygame.image.load(path).convert_alpha()
            images.append(img)
        except Exception as e:
            print(f"Could not load {path}: {e}")
    return images

bg_apartment_images = load_background_images("sprites/background/level1")
bg_apartment_placements = [
    (80, 340, 80, 80),
    (190, 300, 120, 120),
    (350, 350, 40, 70),
    (420, 250, 70, 70),
    (550, 360, 60, 60),
    (650, 350, 50, 70),
    (800, 360, 60, 60)
]

def bg_apartment(screen, cam_x, bg_offset=0):
    screen.fill((163, 111, 64))
    offset = int(bg_offset)

    for i, img in enumerate(bg_apartment_images):
        if i < len(bg_apartment_placements):
            x, y, w, h = bg_apartment_placements[i]
            x = x + offset  # Parallax effect
            img_scaled = pygame.transform.scale(img, (w, h))
            screen.blit(img_scaled, (x, y))

def bg_parallax_forest(screen, cam_x):
    if bg_image2:
        screen.blit(bg_image2, (0,0))
    else:
        screen.fill((80, 140, 80))

def bg_park(screen, cam_x):
    screen.fill((120, 200, 110))
    for x in range(0, WIDTH, 200):
        pygame.draw.rect(screen, (110, 70, 20), (x+80, GROUND_Y - 70, 10, 60))
        pygame.draw.ellipse(screen, (34,139,34), (x+60, GROUND_Y - 100, 50, 50))

# --- Obstacle factories ---
def create_obstacles_lvl1():
    obs = []
    obs.append({'rect': pygame.Rect(150, GROUND_Y - 30, 50, 30), 'type': 'spike'})
    obs.append({'rect': pygame.Rect(350, GROUND_Y-20, 40, 20),  'type': 'spring'})
    obs.append({'rect': pygame.Rect(550, GROUND_Y-120, 80, 20),'type': 'platform'})
    obs.append({'rect': pygame.Rect(480, GROUND_Y-5, 200, 10),  'type': 'water'})
    off = WIDTH
    obs.append({'rect': pygame.Rect(off+150, GROUND_Y-20, 40, 20),  'type': 'spring'})
    obs.append({'rect': pygame.Rect(off+200, GROUND_Y-10, 120, 10), 'type': 'spike'})
    obs.append({'rect': pygame.Rect(off+600, GROUND_Y-60, 60, 60),  'type': 'rotating'})
    return obs

def create_obstacles_lvl2():
    obs = []
    obs.append({'rect': pygame.Rect(100, GROUND_Y-60, 200, 20), 'type': 'platform'})
    obs.append({'rect': pygame.Rect(350, GROUND_Y-30, 40, 30),  'type': 'spring'})
    obs.append({'rect': pygame.Rect(700, GROUND_Y-60, 60, 20),  'type': 'rotating'})
    return obs

def create_obstacles_lvl3():
    obs = []
    obs.append({'rect': pygame.Rect(100, GROUND_Y-10, 100, 10), 'type': 'spike'})
    obs.append({'rect': pygame.Rect(300, GROUND_Y-120, 80, 20),'type': 'platform'})
    obs.append({'rect': pygame.Rect(350, GROUND_Y-30, 40, 20),  'type': 'spring'})
    obs.append({'rect': pygame.Rect(600, GROUND_Y-5, 200, 10), 'type': 'water'})
    return obs

def spawn_enemy():
    x = WIDTH*(SCREENS_PER_LEVEL-1) + WIDTH//2 - ENEMY_WIDTH//2
    y = GROUND_Y - ENEMY_HEIGHT + 10
    return pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)

def spawn_big_boss():
    x = WIDTH*(SCREENS_PER_LEVEL-1) + WIDTH//2 - ENEMY_WIDTH
    y = GROUND_Y - ENEMY_HEIGHT
    return pygame.Rect(x, y, ENEMY_WIDTH*2, ENEMY_HEIGHT*2)

# --- Levels ---
levels = [
    Level(
        background_draw_func=bg_apartment,
        obstacle_factory=create_obstacles_lvl1,
        boss_factory=spawn_enemy,
        clouds=None
    ),
    Level(
        background_draw_func=bg_parallax_forest,
        obstacle_factory=create_obstacles_lvl2,
        boss_factory=spawn_enemy,
        clouds=[[[150, 100], [550, 90], [900, 110]],
                [[320, 60], [700, 80], [1000, 50]]]
    ),
    Level(
        background_draw_func=bg_park,
        obstacle_factory=create_obstacles_lvl3,
        boss_factory=spawn_big_boss,
        clouds=[[[200, 60], [500, 90], [950, 110]],
                [[350, 30], [700, 80], [1000, 100]]]
    ),
]
NUM_LEVELS = len(levels)

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

show_intro()

current_level_idx = 0
level = levels[current_level_idx]

def clone_clouds(cloud_lists):
    return [ [c[0], c[1]] for c in cloud_lists[0] ], [ [c[0], c[1]] for c in cloud_lists[1] ]

obstacles = level.obstacle_factory()
enemy = level.boss_factory()
enemy_alive = True
in_battle = False

player = pygame.Rect(-PLAYER_WIDTH, GROUND_Y-PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT)
player_vel_y = 0

big_clouds, small_clouds = clone_clouds(level.clouds) if level.clouds else ([], [])

anim_state = "idle"
anim_timer = 0
anim_frame = 0
bg_offset = 0  # For apartment parallax

jump_anim_progress = 0
jump_anim_playing = False

# --- Fight Animation State ---
fight_anim_active = False
fight_anim_start = 0
fight_anim_frame = 0

running = True

while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    # --- Events ---
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if in_battle and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_f:
                enemy_alive = False; in_battle = False
                fight_anim_active = True
                fight_anim_start = pygame.time.get_ticks()
                fight_anim_frame = 0
            if e.key == pygame.K_r:
                player.x = -PLAYER_WIDTH; in_battle = False
        if not in_battle and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE and player_vel_y == 0:
                player_vel_y = JUMP_SPEED

    keys = pygame.key.get_pressed()
    old_x, old_y = player.x, player.y

    if not in_battle and not fight_anim_active:
        # Movement
        if keys[pygame.K_LEFT]:
            player.x = max(-PLAYER_WIDTH, player.x - PLAYER_SPEED)
        if keys[pygame.K_RIGHT]:
            player.x += PLAYER_SPEED

        # Horizontal collision
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

        # Gravity
        player_vel_y += GRAVITY
        player.y += player_vel_y

        # Vertical collision/effects
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

        # Ground
        if player.y >= GROUND_Y - PLAYER_HEIGHT:
            player.y = GROUND_Y - PLAYER_HEIGHT
            player_vel_y = 0

        # Encounter
        if enemy_alive and player.colliderect(enemy):
            in_battle = True

    cam_x = max(0, min(player.x + PLAYER_WIDTH//2 - WIDTH//2, LEVEL_WIDTH - WIDTH))

    # Levelwechsel
    if not enemy_alive and player.x >= LEVEL_WIDTH and not fight_anim_active:
        current_level_idx += 1
        if current_level_idx >= NUM_LEVELS:
            break
        level = levels[current_level_idx]
        obstacles = level.obstacle_factory()
        enemy = level.boss_factory()
        enemy_alive = True
        in_battle = False
        player.x, player.y = -PLAYER_WIDTH, GROUND_Y - PLAYER_HEIGHT
        player_vel_y = 0
        big_clouds, small_clouds = clone_clouds(level.clouds) if level.clouds else ([], [])
        bg_offset = 0
        screen.fill(BG_COLOR)
        txt = font.render(f"Level {current_level_idx+1}", True, TEXT_COLOR)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))
        pygame.display.flip()
        pygame.time.wait(2000)

    # --- Parallax movement for apartment background ---
    dx = player.x - old_x
    if current_level_idx == 0:
        bg_offset -= dx * 0.7
        bg_offset = max(min(bg_offset, 200), -200)

    # --- Clouds Parallax Movement ---
    if level.clouds is not None:
        for c in big_clouds:
            c[0] -= dx * 0.5
            if c[0] - cam_x > WIDTH:
                c[0] -= LEVEL_WIDTH
            elif c[0] - cam_x < -200:
                c[0] += LEVEL_WIDTH
        for c in small_clouds:
            c[0] -= dx * (1/3)
            if c[0] - cam_x > WIDTH:
                c[0] -= LEVEL_WIDTH
            elif c[0] - cam_x < -200:
                c[0] += LEVEL_WIDTH

    # --- Drawing ---
    if current_level_idx == 0:
        level.background_draw_func(screen, cam_x, bg_offset)
    else:
        level.background_draw_func(screen, cam_x)

    if level.clouds is not None and cloud_img_big:
        for c in big_clouds:
            screen.blit(cloud_img_big, (c[0] - cam_x, c[1]))
    if level.clouds is not None and cloud_img_small:
        for c in small_clouds:
            screen.blit(cloud_img_small, (c[0] - cam_x, c[1]))

    # Ground
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    # Obstacles
    for o in obstacles:
        r = o['rect']
        typ = o['type']
        img = OBSTACLE_IMAGES.get(typ)
        if typ == 'spring':
            if current_level_idx == 2:
                color = (200, 120, 255)
            elif current_level_idx == 0:
                color = (220, 50, 50)
            else:
                color = OBSTACLE_TYPES[typ]["color"]
        else:
            color = OBSTACLE_TYPES[typ]["color"]
        if img:
            img_scaled = pygame.transform.scale(img, (r.width, r.height))
            screen.blit(img_scaled, (r.x - cam_x, r.y))
        else:
            pygame.draw.rect(screen, color, (r.x - cam_x, r.y, r.width, r.height))

    # --- Fight Animation ---
    if fight_anim_active:
        fight_duration = 2000  # ms
        elapsed = pygame.time.get_ticks() - fight_anim_start
        frame_time = fight_duration // len(fight_frames)
        fight_anim_frame = min(elapsed // frame_time, len(fight_frames) - 1)
        fight_img = fight_frames[fight_anim_frame]
        fight_x = WIDTH//2 - fight_img.get_width()//2
        fight_y = HEIGHT//2 - fight_img.get_height()//2
        screen.blit(fight_img, (fight_x, fight_y))
        if elapsed >= fight_duration:
            fight_anim_active = False
        # Skip all other character drawing during fight
    else:
        # Gegner/Boss
        if enemy_alive and enemy:
            ex, ey = enemy.x - cam_x, enemy.y
            if current_level_idx == 2:
                pygame.draw.rect(screen, (40,220,40), (ex, ey, enemy.width, enemy.height))
            elif enemy_image:
                screen.blit(enemy_image, (ex, ey))
            else:
                pygame.draw.rect(screen, (50,200,50), (ex, ey, ENEMY_WIDTH, ENEMY_HEIGHT))
        # --- Player Animation ---
        if player_vel_y != 0:
            state = "jump"
            if not jump_anim_playing:
                jump_anim_playing = True
                jump_anim_progress = 0
        elif keys[pygame.K_DOWN]:
            state = "crouch"
        elif keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
            state = "walk"
        else:
            state = "idle"
        if player_vel_y == 0:
            jump_anim_playing = False

        facing = "l" if keys[pygame.K_LEFT] else "r"
        if state == "walk":
            frames = walk_frames_l if facing=="l" else walk_frames_r
            n_frames = len(frames)
            if anim_state != state:
                anim_state = state
                anim_frame = 0
                anim_timer = now
            elif now - anim_timer > 100:
                anim_timer = now
                anim_frame = (anim_frame + 1) % n_frames
            current_image = frames[anim_frame]
        elif state == "jump":
            frames = jump_frames_l if facing=="l" else jump_frames_r
            n_frames = len(frames)
            if jump_anim_playing:
                if now - anim_timer > 60 and jump_anim_progress < n_frames - 1:
                    anim_timer = now
                    jump_anim_progress += 1
                current_image = frames[jump_anim_progress]
            else:
                current_image = frames[-1]
        elif state == "crouch":
            frames = crouch_frames_l if facing=="l" else crouch_frames_r
            current_image = frames[0]
            new_h = int(PLAYER_HEIGHT * CROUCH_FACTOR)
            current_image = pygame.transform.scale(current_image, (PLAYER_WIDTH, new_h))
            py = GROUND_Y - new_h
        else:  # idle
            frames = [walk_frames_l[0]] if facing=="l" else [walk_frames_r[0]]
            current_image = frames[0]
        if state != "crouch":
            py = player.y
        screen.blit(current_image, (player.x - cam_x, py))

    # --- UI ---
    info = font.render(
        f"Level {current_level_idx+1}/{NUM_LEVELS}  Screen {cam_x//WIDTH+1}/{SCREENS_PER_LEVEL}",
        True, TEXT_COLOR
    )
    screen.blit(info, (10, 10))
    fps = font.render(f"FPS: {int(clock.get_fps())}", True, TEXT_COLOR)
    screen.blit(fps, (WIDTH-100, 10))

    if in_battle and not fight_anim_active:
        l1 = font.render(f"Level {current_level_idx+1}: Gegner blockiert!", True, TEXT_COLOR)
        l2 = font.render("[F] kämpfen  [R] fliehen", True, TEXT_COLOR)
        screen.blit(l1, (50, 150))
        screen.blit(l2, (50, 180))

    pygame.display.flip()

pygame.quit()
sys.exit()

# main.py
import os
import sys
import math
import argparse
from pathlib import Path
import pygame
from dialog_ui import DialogueBox

# ---------- CONFIG (windowed placeholders; can be overridden by -f) ----------
WIDTH, HEIGHT = 1366, 768 
FPS = 60
TILE = 16

# ---------- Project-relative paths ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR   = PROJECT_ROOT / "assets"
BANK_ASSET_DIR = ASSETS_DIR / "bank"
GENERAL_ASSET_DIR = ASSETS_DIR / "general"
FONTS_DIR    = ASSETS_DIR / "fonts"

# Asset files (relative to project)
CORNER_IMG_PATH = GENERAL_ASSET_DIR / "bottom_left_corner.png"
EDGE_IMG_PATH   = GENERAL_ASSET_DIR / "edge.png"
FONT_PATH       = FONTS_DIR / "PressStart2P-Regular.ttf"

# Visual layout (game room)
WALL_H = 128
FLOOR_TILE_TARGET = 160
PLAYER_SIZE = 32
PLAYER_SPEED = 4
BUTTON_TARGET_H = 40
BUTTON_OFFSET_Y = 20
BUTTON_SPACING_X = 110
DOOR_MARGIN = 12

# Lighting
DARK_ENABLED = True
DARK_ALPHA = 200
VISION_LENGTH = 240
FOV_DEG = 65
SOFT_EDGE = True
FEATHER_STEPS = 8

# Fade after button press
FADE_TO_BLACK_MS = 900

# ---------- INTRO DIALOGUE ----------
INTRO_TEXT = ("Dans la banque, le braquage s’est mal passé, Tony, chef d’une grande famille mafieuse "
              "a fait le choix de faire lui-même un braquage, sauf que ça a mal tourné les sirènes "
              "de police retentissent, il doit vite s’échapper dans son oreillette, son acolyte "
              "‘Lukas” le policier corrompu")

# Dialogue box layout rules (your latest)
FONT_SIZE = 32
LINE_HEIGHT_FACTOR = 1.6
PADDING_LEFT   = 20
PADDING_RIGHT  = 40
PADDING_TOP    = 20
PADDING_BOTTOM = 20
BOX_FILL_COLOR = (34, 34, 34)   # #222

# -------------- CLI --------------
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--fullscreen", action="store_true", help="Use fullscreen display mode")
    return ap.parse_args()

# -------------- Helpers --------------
def load_image(path: Path):
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception as e:
        print(f"Failed to load {path}: {e}")
        sys.exit(1)

def load_bank_image(name: str):
    return load_image(BANK_ASSET_DIR / name)

def scale_to_width(img, width):
    w, h = img.get_size()
    new_h = int(round(h * (width / w)))
    return pygame.transform.scale(img, (width, new_h))

def scale_to_height(img, height):
    w, h = img.get_size()
    new_w = int(round(w * (height / h)))
    return pygame.transform.scale(img, (new_w, height))

def crop_center(img, crop_w, crop_h):
    w, h = img.get_size()
    x = max(0, (w - crop_w) // 2)
    y = max(0, (h - crop_h) // 2)
    rect = pygame.Rect(x, y, crop_w, crop_h)
    return img.subsurface(rect).copy()

# ---------- Darkness helpers (cone subtraction) ----------
def angle_to_vec(angle_deg):
    rad = math.radians(angle_deg)
    return math.cos(rad), math.sin(rad)

def cone_polygon(origin, angle_deg, fov_deg, length, arc_segments=18):
    ox, oy = origin
    half = fov_deg / 2.0
    start = angle_deg - half
    end = angle_deg + half
    pts = [origin]
    for i in range(arc_segments + 1):
        t = i / arc_segments
        a = start + t * (end - start)
        dx, dy = angle_to_vec(a)
        pts.append((ox + dx * length, oy + dy * length))
    return pts

def subtract_polygon_alpha(base_surf, poly_points, subtract_amount):
    if subtract_amount <= 0:
        return
    temp = pygame.Surface(base_surf.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(temp, (255, 255, 255, subtract_amount), poly_points)
    base_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

def make_darkness_cone(size, alpha, origin, angle_deg, fov_deg, length,
                       soft=True, feather_steps=8):
    w, h = size
    darkness = pygame.Surface((w, h), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, alpha))
    if not soft:
        poly = cone_polygon(origin, angle_deg, fov_deg, length)
        subtract_polygon_alpha(darkness, poly, 255)
        return darkness
    inner_fov = fov_deg * 0.7
    inner_len = length * 0.85
    inner_poly = cone_polygon(origin, angle_deg, inner_fov, inner_len)
    subtract_polygon_alpha(darkness, inner_poly, 255)
    for i in range(feather_steps):
        t = (i + 1) / feather_steps
        fov_i = inner_fov + t * (fov_deg - inner_fov)
        len_i = inner_len + t * (length - inner_len)
        amt = int((1.0 - t) * 200)
        if amt <= 0: continue
        poly_i = cone_polygon(origin, angle_deg, fov_i, len_i)
        subtract_polygon_alpha(darkness, poly_i, amt)
    return darkness

# ---------- UI helpers ----------
def draw_alert_box(surface, text, center, font):
    padding = 14
    txt = font.render(text, True, (255, 255, 255))
    box_w, box_h = txt.get_width() + padding * 2, txt.get_height() + padding * 2
    box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(box_surf, (0, 0, 0, 210), (0, 0, box_w, box_h), border_radius=8)
    pygame.draw.rect(box_surf, (255, 255, 255, 220), (0, 0, box_w, box_h), width=2, border_radius=8)
    surface.blit(box_surf, (center[0] - box_w // 2, center[1] - box_h // 2))
    surface.blit(txt, (center[0] - txt.get_width() // 2, center[1] - txt.get_height() // 2))

def pulsating_alpha(t, min_a=70, max_a=220, speed=2.0):
    s = (math.sin(t * speed) + 1) * 0.5
    return int(min_a + s * (max_a - min_a))

def draw_button_glow(screen, rect, alpha):
    glow = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    outline1 = rect.inflate(16, 16)
    outline2 = rect.inflate(8, 8)
    pygame.draw.rect(glow, (255, 255, 255, int(alpha * 0.5)), outline1, width=3, border_radius=10)
    pygame.draw.rect(glow, (255, 255, 255, alpha),           outline2, width=2, border_radius=8)
    screen.blit(glow, (0, 0))

# ---------- Collision helpers ----------
def move_and_collide(player, dx, dy, obstacles):
    if dx != 0:
        player.x += dx
        for ob in obstacles:
            if player.colliderect(ob):
                if dx > 0: player.right = ob.left
                else:      player.left = ob.right
    if dy != 0:
        player.y += dy
        for ob in obstacles:
            if player.colliderect(ob):
                if dy > 0: player.bottom = ob.top
                else:      player.top = ob.bottom

def main():
    args = parse_args()
    pygame.init()

    # -------- Display mode --------
    if args.fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        win_w, win_h = screen.get_size()
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        win_w, win_h = WIDTH, HEIGHT

    clock = pygame.time.Clock()
    pygame.display.set_caption("Intro (segments) + Bank Vault Room")

    # ---- Dialogue UI (uses project-relative paths) ----
    dialog = DialogueBox(
        screen_w=win_w,
        screen_h=win_h,
        font_path=FONT_PATH,                      # Path object is fine
        font_size=32,
        line_height_factor=1.6,
        padding_left=20, padding_right=40, padding_top=20, padding_bottom=20,
        corner_img_path=CORNER_IMG_PATH,
        edge_img_path=EDGE_IMG_PATH,
        tile=TILE,
        fill_color=(34, 34, 34)
    )
    dialog.set_text(INTRO_TEXT)

    # ---- Load game assets (project-relative) ----
    floor_raw = load_bank_image("floor_tile_1.png")
    wall_raw  = load_bank_image("wall.png")
    door_closed_raw = load_bank_image("door_closed.png")
    door_opened_raw = load_bank_image("door_opened.png")
    red_btn_up_raw      = load_bank_image("red_btn_not_pressed.png")
    red_btn_down_raw    = load_bank_image("red_btn_pressed.png")
    green_btn_up_raw    = load_bank_image("green_btn_not_pressed.png")
    green_btn_down_raw  = load_bank_image("green_btn_pressed.png")

    floor_tile = crop_center(floor_raw, FLOOR_TILE_TARGET, FLOOR_TILE_TARGET)
    wall_img = pygame.transform.scale(wall_raw, (win_w, WALL_H))

    max_door_h = max(1, WALL_H - DOOR_MARGIN * 2)
    door_closed_img = scale_to_height(door_closed_raw, max_door_h)
    if door_closed_img.get_width() > win_w - DOOR_MARGIN * 2:
        door_closed_img = scale_to_width(door_closed_img, win_w - DOOR_MARGIN * 2)
    door_opened_img = scale_to_height(door_opened_raw, max_door_h)
    if door_opened_img.get_width() > win_w - DOOR_MARGIN * 2:
        door_opened_img = scale_to_width(door_opened_img, win_w - DOOR_MARGIN * 2)

    door_img = door_closed_img
    door_rect = door_img.get_rect()
    door_rect.centerx = win_w // 2
    door_rect.centery = WALL_H // 2

    red_btn_up   = scale_to_height(red_btn_up_raw, BUTTON_TARGET_H)
    red_btn_down = scale_to_height(red_btn_down_raw, BUTTON_TARGET_H)
    green_btn_up   = scale_to_height(green_btn_up_raw, BUTTON_TARGET_H)
    green_btn_down = scale_to_height(green_btn_down_raw, BUTTON_TARGET_H)

    red_btn_img = red_btn_up
    green_btn_img = green_btn_up

    red_btn_rect = red_btn_img.get_rect()
    green_btn_rect = green_btn_img.get_rect()
    base_y = WALL_H + BUTTON_OFFSET_Y
    red_btn_rect.midtop = (door_rect.centerx - BUTTON_SPACING_X, base_y)
    green_btn_rect.midtop = (door_rect.centerx + BUTTON_SPACING_X, base_y)
    red_collide = red_btn_rect.inflate(6, 6)
    green_collide = green_btn_rect.inflate(6, 6)

    # Player & game state
    player = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
    player.center = (win_w // 2, win_h - PLAYER_SIZE - 20)
    player_color = (40, 200, 80)
    facing_angle = -90.0
    TOP_PLAY_LIMIT = WALL_H + 4
    door_open = False
    red_pressed = False
    green_pressed = False
    fade_started = False
    fade_start_time = 0

    STATE_INTRO = 0
    STATE_GAME = 1
    state = STATE_INTRO

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        t_sec = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == STATE_INTRO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        done = dialog.advance()
                        if done:
                            state = STATE_GAME

            elif state == STATE_GAME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_d:
                        global DARK_ENABLED
                        DARK_ENABLED = not DARK_ENABLED
                    elif event.key == pygame.K_UP:
                        facing_angle = -90.0
                    elif event.key == pygame.K_DOWN:
                        facing_angle = 90.0
                    elif event.key == pygame.K_LEFT:
                        facing_angle = 180.0
                    elif event.key == pygame.K_RIGHT:
                        facing_angle = 0.0
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not door_open:
                    mx, my = event.pos
                    if red_btn_rect.collidepoint(mx, my):
                        red_pressed = True
                        red_btn_img = red_btn_down
                        door_open = True
                        fade_started = True
                        fade_start_time = pygame.time.get_ticks()
                    elif green_btn_rect.collidepoint(mx, my):
                        green_pressed = True
                        green_btn_img = green_btn_down
                        door_open = True
                        fade_started = True
                        fade_start_time = pygame.time.get_ticks()

        # ---------- DRAW ----------
        if state == STATE_INTRO:
            screen.fill((10, 10, 12))
            dialog.draw(screen, color=(255, 255, 255))

        else:  # STATE_GAME
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * PLAYER_SPEED
            dy = (keys[pygame.K_DOWN]  - keys[pygame.K_UP])   * PLAYER_SPEED
            if dx or dy:
                if abs(dx) > abs(dy):
                    facing_angle = 0.0 if dx > 0 else 180.0
                    dy = 0
                else:
                    facing_angle = 90.0 if dy > 0 else -90.0
                    dx = 0

            obstacles = [red_collide, green_collide]
            move_and_collide(player, dx, dy, obstacles)
            if player.left < 0: player.left = 0
            if player.right > win_w: player.right = win_w
            if player.top < TOP_PLAY_LIMIT: player.top = TOP_PLAY_LIMIT
            if player.bottom > win_h: player.bottom = win_h

            # World
            screen.fill((20, 24, 28))
            tile_w, tile_h = floor_tile.get_size()
            for y in range(0, win_h, tile_h):
                for x in range(0, win_w, tile_w):
                    screen.blit(floor_tile, (x, y))
            screen.blit(wall_img, (0, 0))
            door_img = door_opened_img if door_open else door_closed_img
            screen.blit(door_img, (win_w // 2 - door_img.get_width() // 2,
                                   WALL_H // 2 - door_img.get_height() // 2))
            screen.blit(red_btn_img, red_btn_rect.topleft)
            screen.blit(green_btn_img, green_btn_rect.topleft)
            pygame.draw.rect(screen, (40, 200, 80), player)

            # Prompt zone (unchanged)
            between_x = (player.centerx > red_btn_rect.right) and (player.centerx < green_btn_rect.left)
            near_y = player.top <= red_btn_rect.bottom + 40 and player.bottom >= red_btn_rect.top - 100
            facing_up = (abs(facing_angle + 90.0) < 1e-3)
            show_prompt = (between_x and near_y and facing_up and not door_open)
            if show_prompt:
                alpha = pulsating_alpha(t_sec, 90, 220, 2.2)
                # Note: draw_button_glow is defined above in this file
                # You can keep your glow + alert box if desired

            pygame.draw.line(screen, (0, 0, 0), (0, WALL_H), (win_w, WALL_H), 2)

            if DARK_ENABLED:
                if fade_started:
                    elapsed = pygame.time.get_ticks() - fade_start_time
                    if elapsed >= FADE_TO_BLACK_MS:
                        blackout = pygame.Surface((win_w, win_h))
                        blackout.fill((0, 0, 0))
                        screen.blit(blackout, (0, 0))
                    else:
                        origin = player.center
                        cone_overlay = make_darkness_cone(
                            (win_w, win_h), DARK_ALPHA, origin,
                            facing_angle, FOV_DEG, VISION_LENGTH,
                            SOFT_EDGE, FEATHER_STEPS
                        )
                        screen.blit(cone_overlay, (0, 0))
                        k = min(1.0, elapsed / FADE_TO_BLACK_MS)
                        fade_alpha = int(k * 255)
                        fade_layer = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
                        fade_layer.fill((0, 0, 0, fade_alpha))
                        screen.blit(fade_layer, (0, 0))
                else:
                    origin = player.center
                    cone_overlay = make_darkness_cone(
                        (win_w, win_h), DARK_ALPHA, origin,
                        facing_angle, FOV_DEG, VISION_LENGTH,
                        SOFT_EDGE, FEATHER_STEPS
                    )
                    screen.blit(cone_overlay, (0, 0))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
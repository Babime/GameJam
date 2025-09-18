
from __future__ import annotations
from pathlib import Path
import sys
import pygame

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import (
    ASSETS_DIR, WIDTH, HEIGHT, FPS, TILE,
    FONT_PATH, CORNER_IMG_PATH, EDGE_IMG_PATH,
    FONT_SIZE, LINE_HEIGHT_FACTOR, PADDING_LEFT, PADDING_RIGHT, PADDING_TOP, PADDING_BOTTOM,
    BOX_FILL_COLOR, BANK_ASSET_DIR, INITIAL_TRUST, INITIAL_POLICE_GAP, RNG_SEED, SCENE_INTRO_BLACK_MS
)

from dialog_ui import DialogueBox
from dialogue_engine import GameVars
from core.scene_runner import run_scene

# --- import your scene content & room(s) ---
from scenes.scene1_vault import SCENE1_VAULT
from scenes.vault_room import VaultRoomScene
from scenes.scene3_country_house import SCENE3_MARTHA
from scenes.country_house_scene import CountryHouseScene

# NEW: Scene 2 (street) dialogue + minimal static room
from scenes.scene2_street import SCENE2_STREET
from scenes.street_scene2_static import StreetScene2Static


def show_start_screen(screen, WIDTH, HEIGHT):
    pygame.init()
    clock = pygame.time.Clock()

    font = pygame.font.Font(FONT_PATH, 48)
    small_font = pygame.font.Font(FONT_PATH, 28)
    tiny_font = pygame.font.Font(FONT_PATH, 20)

    # === IMAGES ===
    bg_img = pygame.image.load("./assets/general/bg_city_start.png").convert()
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))

    plane_img = pygame.image.load("./assets/general/plane.png").convert_alpha()
    plane_img = pygame.transform.scale(
        plane_img, (plane_img.get_width() // 6, plane_img.get_height() // 6)
    )
    plane_rect = plane_img.get_rect(midright=(WIDTH + 50, 50))

    tony_img1 = pygame.image.load("./assets/general/walk_to_his_right_1.png").convert_alpha()
    tony_img2 = pygame.image.load("./assets/general/walk_to_his_right_2.png").convert_alpha()
    tony_frames = [tony_img1, tony_img2]
    tony_frame_index = 0
    tony_anim_timer = 0
    tony_rect = tony_img1.get_rect(midbottom=(0, HEIGHT - 20))

    plane_speed = 3
    tony_speed = 8  

    while True:
        # === FOND BLEU NUIT ===
        screen.fill((10, 15, 35))  
        screen.blit(bg_img, (0, 0))

        # === ANIMATIONS ===
        plane_rect.x -= plane_speed
        if plane_rect.right < 0:
            plane_rect.left = WIDTH + 100

        tony_rect.x += tony_speed
        if tony_rect.left > WIDTH:
            tony_rect.right = 0

        tony_anim_timer += 1
        if tony_anim_timer >= 10:
            tony_anim_timer = 0
            tony_frame_index = (tony_frame_index + 1) % len(tony_frames)
        current_tony = tony_frames[tony_frame_index]

        # === TEXTES ===
        title = font.render("SHADOW TONY", True, (255, 255, 255))
        subtitle = small_font.render("Can he get out ?", True, (200, 200, 200))
        group_text = tiny_font.render("GROUPE 16", True, (120, 120, 255))
        quit_text = tiny_font.render("Appuie sur Q pour quitter", True, (200, 180, 180))

        # === POSITIONNEMENTS ===
        title_y = HEIGHT // 2 - 200
        subtitle_y = HEIGHT // 2 - 120

        # Bouton entre le sous-titre et "quit"
        spacing = 60
        btn_w, btn_h = 340, 70
        btn_x = (WIDTH - btn_w) // 2
        btn_y = subtitle_y + spacing
        start_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        quit_y = btn_y + btn_h + 50  # un peu plus haut que dans ta version

        # === BOUTON START ===
        pygame.draw.rect(screen, (60, 180, 80), start_rect, border_radius=12)
        btn_text = small_font.render("START GAME", True, (0, 0, 0))
        text_rect = btn_text.get_rect(center=start_rect.center)

        # === DESSINS ===
        screen.blit(plane_img, plane_rect)
        screen.blit(current_tony, tony_rect)

        screen.blit(title, ((WIDTH - title.get_width()) // 2, title_y))
        screen.blit(subtitle, ((WIDTH - subtitle.get_width()) // 2, subtitle_y))
        screen.blit(btn_text, text_rect)
        screen.blit(group_text, (10, 10))

        quit_rect = quit_text.get_rect(center=(WIDTH // 2, quit_y))
        screen.blit(quit_text, quit_rect)

        pygame.display.flip()
        clock.tick(60)

        # === EVENTS ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    return


def _run_country_house_debug(screen, gvars):
    import pygame
    from scenes.country_house_scene import CountryHouseScene
    from core.config import FPS

    scene = CountryHouseScene(win_w=screen.get_width(), win_h=screen.get_height(), gvars=gvars)

    def _after_arrival(_):
        scene.start_event("tony_exit_car", on_done=lambda __:
            scene.start_event("martha_exit_house", on_done=lambda ___:
                scene.start_event("martha_greets", on_done=lambda ____: None)
            )
        )

    scene.start_event("arrival_from_top", on_done=_after_arrival)

    clock = pygame.time.Clock()
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_a:
                    scene.start_event("arrival_from_top", on_done=_after_arrival)
                elif ev.key == pygame.K_m:
                    # If you want to just pop her out correctly:
                    scene.start_event("martha_exit_house", on_done=lambda __:
                        scene.start_event("martha_greets", on_done=lambda ___: None)
                    )
                elif ev.key == pygame.K_r:
                    scene.start_event("rest_living_room", on_done=lambda __: None)
                elif ev.key == pygame.K_d:
                    scene.start_event("harold_arrives_chase", on_done=lambda __: None)

        dt = clock.tick(FPS)
        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()


def make_room_scene1(win_w, win_h, gvars):
    return VaultRoomScene(
        win_w=win_w, win_h=win_h,
        bank_asset_dir=BANK_ASSET_DIR,
        hud_font_path=FONT_PATH,
        game_vars=gvars
    )

# Kept as-is for the country house (Martha) scene
def make_room_scene2(win_w, win_h, gvars):
    return CountryHouseScene(win_w, win_h, gvars)

# NEW: minimal static room factory for Scene 2 (street)
def make_room_scene2_street(win_w, win_h, gvars):
    return StreetScene2Static(win_w, win_h, gvars)


# Only run Scene 2 (street). Other scenes are left commented out.
CAMPAIGN = [
    {"id": "scene1_vault", "scene": SCENE1_VAULT, "room_factory": make_room_scene1},
    {"id": "scene2_street", "scene": SCENE2_STREET, "room_factory": make_room_scene2_street},
    {"id": "martha_scene", "scene": SCENE3_MARTHA, "room_factory": make_room_scene2},
]



def _black_pause(screen: pygame.Surface, ms: int):
    clock = pygame.time.Clock()
    elapsed = 0
    while elapsed < ms:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        screen.fill((0, 0, 0))
        pygame.display.flip()
        elapsed += clock.tick(FPS)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tony – Campaign")

    show_start_screen(screen, WIDTH, HEIGHT)

    dialog = DialogueBox(
        screen_w=WIDTH, screen_h=HEIGHT,
        font_path=FONT_PATH, font_size=FONT_SIZE, line_height_factor=LINE_HEIGHT_FACTOR,
        padding_left=PADDING_LEFT, padding_right=PADDING_RIGHT,
        padding_top=PADDING_TOP, padding_bottom=PADDING_BOTTOM,
        corner_img_path=CORNER_IMG_PATH, edge_img_path=EDGE_IMG_PATH, tile=TILE,
        fill_color=BOX_FILL_COLOR
    )

    # Shared game state across all scenes
    gvars = GameVars(trust=INITIAL_TRUST, police_gap=INITIAL_POLICE_GAP)

    if "--scene2" in sys.argv or "--country-house" in sys.argv:
        _run_country_house_debug(screen, gvars)
        pygame.quit()
        return

    for entry in CAMPAIGN:
        _black_pause(screen, SCENE_INTRO_BLACK_MS)
        scene_def = entry["scene"]
        factory   = entry["room_factory"]
        run_scene(screen, dialog, scene_def, factory, gvars, fps=FPS, rng_seed=None)
        # Allow early quit
        for ev in pygame.event.get(pygame.QUIT):
            pygame.quit()
            return

    pygame.quit()


if __name__ == "__main__":
    main()

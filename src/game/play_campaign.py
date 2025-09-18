from __future__ import annotations
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pygame
from audio.bgm import play_bgm


from core.config import (
    ASSETS_DIR, WIDTH, HEIGHT, FPS, TILE,
    FONT_PATH, CORNER_IMG_PATH, EDGE_IMG_PATH,
    FONT_SIZE, LINE_HEIGHT_FACTOR, PADDING_LEFT, PADDING_RIGHT, PADDING_TOP, PADDING_BOTTOM,
    BOX_FILL_COLOR, BANK_ASSET_DIR, INITIAL_TRUST, INITIAL_POLICE_GAP, RNG_SEED, SCENE_INTRO_BLACK_MS
)

from scenes.scene_airport_dialogue import SCENE_AIRPORT_CAUGHT, SCENE_AIRPORT_ESCAPED
from scenes.airport_room import AirportRoomScene
from core.scene_helpers import select_airport_scene

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


def show_start_screen(screen, WIDTH, HEIGHT, fade_in_ms: int = 0):
    clock = pygame.time.Clock()

    # --- Fonts ---
    font = pygame.font.Font(FONT_PATH, 48)
    small_font = pygame.font.Font(FONT_PATH, 28)
    tiny_font = pygame.font.Font(FONT_PATH, 20)

    # --- Images ---
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

    # --- Static layout for texts & button ---
    title_y = HEIGHT // 2 - 200
    subtitle_y = HEIGHT // 2 - 120

    spacing = 60
    btn_w, btn_h = 340, 70
    btn_x = (WIDTH - btn_w) // 2
    btn_y = subtitle_y + spacing
    start_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    quit_y = btn_y + btn_h + 50

    # --- Motion params (frame-based like your original) ---
    plane_speed = 3   # px/frame
    tony_speed = 8    # px/frame

    # --- Fade overlay ---
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0))
    fade_elapsed = 0
    fading = fade_in_ms > 0

    running = True
    while running:
        dt = clock.tick(60)

        # --- Input ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_rect.collidepoint(event.pos):
                    return

        # --- Update animations ---
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

        # --- Draw ---
        screen.fill((10, 15, 35))
        screen.blit(bg_img, (0, 0))

        # moving bits
        screen.blit(plane_img, plane_rect)
        screen.blit(current_tony, tony_rect)

        # texts
        title = font.render("SHADOW TONY", True, (255, 255, 255))
        subtitle = small_font.render("Can he get out ?", True, (200, 200, 200))
        group_text = tiny_font.render("GROUPE 16", True, (120, 120, 255))
        quit_text = tiny_font.render("Appuie sur Q pour quitter", True, (200, 180, 180))

        screen.blit(title, ((WIDTH - title.get_width()) // 2, title_y))
        screen.blit(subtitle, ((WIDTH - subtitle.get_width()) // 2, subtitle_y))
        screen.blit(group_text, (10, 10))

        # start button (hover highlight)
        hover = start_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = (80, 200, 100) if hover else (60, 180, 80)
        pygame.draw.rect(screen, btn_color, start_rect, border_radius=12)
        pygame.draw.rect(screen, (0, 0, 0), start_rect, width=2, border_radius=12)
        btn_text = small_font.render("START GAME", True, (0, 0, 0))
        text_rect = btn_text.get_rect(center=start_rect.center)
        screen.blit(btn_text, text_rect)

        # quit hint
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, quit_y))
        screen.blit(quit_text, quit_rect)

        # fade-in overlay on top
        if fading:
            fade_elapsed += dt
            # t goes 1 -> 0 during the fade duration
            t = max(0.0, min(1.0, 1.0 - (fade_elapsed / float(fade_in_ms))))
            overlay.set_alpha(int(255 * t))
            screen.blit(overlay, (0, 0))
            if fade_elapsed >= fade_in_ms:
                fading = False

        pygame.display.flip()

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


def make_room_scene2_street(win_w, win_h, gvars):
    return StreetScene2Static(win_w, win_h, gvars)


def make_room_airport(win_w, win_h, gvars):
    return AirportRoomScene(
        win_w=win_w,
        win_h=win_h,
        gvars=gvars,
        hud_font_path=FONT_PATH
    )

CAMPAIGN = [
    #{"id": "scene1_vault", "scene": SCENE1_VAULT, "room_factory": make_room_scene1},
    #{"id": "scene2_street", "scene": SCENE2_STREET, "room_factory": make_room_scene2_street, "bgm": "scene2.mp3", "bgm_volume": 0.6},
    #{"id": "martha_scene",  "scene": SCENE3_MARTHA, "room_factory": make_room_scene2, "bgm": "scene3.mp3", "bgm_volume": 0.6},
    {"id": "scene4_airport","scene": select_airport_scene, "room_factory": make_room_airport, "bgm": "scene4.mp3", "bgm_volume": 0.5},
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


def run_end_sequence(screen: pygame.Surface, dialog: DialogueBox, outcome: str):
    """End screen with 3 messages; advance on SPACE like normal dialogue.
    On the last SPACE, fade to the start screen and wait for a new Start."""
    # Cut current music fast
    try:
        pygame.mixer.music.fadeout(400)
    except Exception:
        pass

    try:
        pygame.mixer.fadeout(400)
    except Exception:
        pass

    clock = pygame.time.Clock()

    # Messages (short enough but still paginated if they ever get long)
    messages = [
        "Tony a réussi à s’échapper" if outcome == "escaped" else "Tony a été capturé",
        "En êtes-vous la cause, ou bien Tony mérite-t-il ce résultat après ne pas vous avoir fait confiance ?",
        "..."
    ]

    idx = 0
    dialog.set_text(messages[idx])

    running = True
    while running:
        dt = clock.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                    # First paginate within the same bubble
                    done_page = dialog.advance()
                    if done_page:
                        # Move to next message (or finish if that was the last)
                        idx += 1
                        if idx >= len(messages):
                            running = False
                            break
                        dialog.set_text(messages[idx])

        # Draw: black + dialogue box
        screen.fill((0, 0, 0))
        dialog.draw(screen, color=(255, 255, 255))
        pygame.display.flip()

    # Restart menu music and fade into start screen; return when the player presses Start
    show_start_screen(screen, WIDTH, HEIGHT, fade_in_ms=1200)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tony – Campaign")

    first_cycle = True  # first time we show the menu without our manual fade

    while True:
        # --- Show the start menu and play the title music ---
        play_bgm("scene1.mp3", volume=0.5)
        show_start_screen(screen, WIDTH, HEIGHT, fade_in_ms=0 if first_cycle else 1200)

        # Fresh dialogue box & game variables for a new run
        dialog = DialogueBox(
            screen_w=WIDTH, screen_h=HEIGHT,
            font_path=FONT_PATH, font_size=FONT_SIZE, line_height_factor=LINE_HEIGHT_FACTOR,
            padding_left=PADDING_LEFT, padding_right=PADDING_RIGHT,
            padding_top=PADDING_TOP, padding_bottom=PADDING_BOTTOM,
            corner_img_path=CORNER_IMG_PATH, edge_img_path=EDGE_IMG_PATH, tile=TILE,
            fill_color=BOX_FILL_COLOR
        )
        gvars = GameVars(trust=INITIAL_TRUST, police_gap=INITIAL_POLICE_GAP)

        # (Optional debug jumps stay the same)
        if "--scene2" in sys.argv or "--country-house" in sys.argv:
            _run_country_house_debug(screen, gvars)
            pygame.quit()
            return

        # --- Run the campaign once ---
        for entry in CAMPAIGN:
            _black_pause(screen, SCENE_INTRO_BLACK_MS)

            scene_def_or_fn = entry["scene"]
            scene_def = scene_def_or_fn(gvars) if callable(scene_def_or_fn) else scene_def_or_fn
            factory = entry["room_factory"]

            bgm_name = entry.get("bgm")
            if bgm_name:
                play_bgm(bgm_name, volume=float(entry.get("bgm_volume", 0.7)))

            run_scene(screen, dialog, scene_def, factory, gvars, fps=FPS, rng_seed=None)

            for ev in pygame.event.get(pygame.QUIT):
                pygame.quit()
                return

        # --- When the campaign ends, play the end sequence, then loop to replay ---
        outcome = gvars.flags.get("ending", "caught")  # default if not set
        run_end_sequence(screen, dialog, outcome)
        first_cycle = False


if __name__ == "__main__":
    main()

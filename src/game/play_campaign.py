
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

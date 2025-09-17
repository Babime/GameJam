# src/game/play_campaign.py
from __future__ import annotations
from pathlib import Path
import sys
import pygame

# QUICK-FIX for direct execution; remove if you run with: python -m game.play_campaign from /src
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import (
    WIDTH, HEIGHT, FPS, TILE,
    FONT_PATH, CORNER_IMG_PATH, EDGE_IMG_PATH,
    FONT_SIZE, LINE_HEIGHT_FACTOR, PADDING_LEFT, PADDING_RIGHT, PADDING_TOP, PADDING_BOTTOM,
    BOX_FILL_COLOR, BANK_ASSET_DIR, INITIAL_TRUST, INITIAL_POLICE_GAP, RNG_SEED
)

from dialog_ui import DialogueBox
from dialogue_engine import GameVars
from core.scene_runner import run_scene

# --- import your scene content & room(s) ---
from scenes.scene1_vault import SCENE1_VAULT
from scenes.vault_room import VaultRoomScene

def make_room_scene1(win_w, win_h, gvars):
    return VaultRoomScene(
        win_w=win_w, win_h=win_h,
        bank_asset_dir=BANK_ASSET_DIR,
        hud_font_path=FONT_PATH,
        game_vars=gvars
    )

CAMPAIGN = [
    {"id": "scene1_vault", "scene": SCENE1_VAULT, "room_factory": make_room_scene1},
    # {"id": "scene2_xyz", "scene": SCENE2, "room_factory": make_room_scene2},
    # {"id": "scene3_abc", "scene": SCENE3, "room_factory": make_room_scene3},
]

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

    for entry in CAMPAIGN:
        scene_def = entry["scene"]
        factory   = entry["room_factory"]
        run_scene(screen, dialog, scene_def, factory, gvars, fps=FPS, rng_seed=RNG_SEED)
        # Allow early quit
        for ev in pygame.event.get(pygame.QUIT):
            pygame.quit()
            return

    pygame.quit()

if __name__ == "__main__":
    main()